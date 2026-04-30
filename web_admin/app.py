import os
import sys
# Ensure we can import config and database from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import time
import requests
from functools import wraps

from config import ADMIN_PASSWORD, BOT_TOKEN, LANG
from database import Database

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
db = Database()

@app.template_filter('datetime')
def format_datetime(value):
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(value))

def send_telegram_msg(chat_id, text):
    """Helper to send telegram messages from the web panel."""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(api_url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }, timeout=2)
    except:
        pass

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Logged in successfully.', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        else:
            flash('Invalid admin password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    users, active, queue = db.get_global_stats()
    total_posts = db.get_wall_post_count()
    return render_template('dashboard.html', users=users, active=active, queue=queue, total_posts=total_posts)

@app.route('/users')
@login_required
def users_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    limit = 20
    offset = (page - 1) * limit
    
    c = db.conn.cursor()
    if search:
        if search.isdigit():
            c.execute("SELECT * FROM users WHERE user_id = ? OR first_name LIKE ? ORDER BY last_active DESC LIMIT ? OFFSET ?", (int(search), f"%{search}%", limit, offset))
        else:
            c.execute("SELECT * FROM users WHERE first_name LIKE ? OR username LIKE ? ORDER BY last_active DESC LIMIT ? OFFSET ?", (f"%{search}%", f"%{search}%", limit, offset))
        
        # Count for search
        count_c = db.conn.cursor()
        if search.isdigit():
            count_c.execute("SELECT COUNT(*) FROM users WHERE user_id = ? OR first_name LIKE ?", (int(search), f"%{search}%"))
        else:
            count_c.execute("SELECT COUNT(*) FROM users WHERE first_name LIKE ? OR username LIKE ?", (f"%{search}%", f"%{search}%"))
        total_items = count_c.fetchone()[0]
    else:
        c.execute("SELECT * FROM users ORDER BY last_active DESC LIMIT ? OFFSET ?", (limit, offset))
        total_items = db.get_user_count()
        
    total_pages = (total_items + limit - 1) // limit
    users = [dict(row) for row in c.fetchall()]
    
    # Sanitize data for web display (Prevent Zalgo breakage)
    for u in users:
        if u['first_name'] and len(u['first_name']) > 50:
            u['first_name'] = u['first_name'][:47] + "..."
        if u['username'] and len(u['username']) > 50:
            u['username'] = u['username'][:47] + "..."
            
    return render_template('users.html', users=users, page=page, total_pages=total_pages, search=search, total_items=total_items)

@app.route('/users/<action>/<int:user_id>', methods=['POST'])
@login_required
def user_action(action, user_id):
    if action == 'ban':
        db.ban_user(user_id, reason="Banned via Web Admin Panel")
        
        # Notify Banned User 
        send_telegram_msg(user_id, LANG['ban_notification'])
        
        # Notify Reporters
        reporters = db.get_user_reporters(user_id)
        for rep_id in reporters:
            send_telegram_msg(rep_id, LANG['report_success_notification'])
            
        flash(f'User {user_id} banned successfully. Notifications sent.', 'success')
    elif action == 'unban':
        db.update_user(user_id, {'is_banned': 0})
        send_telegram_msg(user_id, LANG['unban_notification'])
        flash(f'User {user_id} unbanned successfully. Notification sent.', 'success')
    elif action == 'vip':
        user = db.get_user(user_id)
        if user:
            new_vip = 0 if user['is_vip'] else 1
            db.update_user(user_id, {'is_vip': new_vip})
            action_text = "granted" if new_vip else "revoked"
            flash(f'VIP status {action_text} for User {user_id}.', 'success')
            
    return redirect(request.referrer or url_for('users_list'))

@app.route('/promos', methods=['GET', 'POST'])
@login_required
def promo_manager():
    if request.method == 'POST':
        code = request.form.get('code', '').upper().strip()
        promo_type = request.form.get('type', 'coins')
        amount = request.form.get('amount', 0, type=int)
        max_uses = request.form.get('max_uses', 10, type=int)
        
        if not code:
            flash('Code name is required.', 'error')
        else:
            db.create_promo_admin(code, promo_type, amount, max_uses)
            flash(f'Promo code {code} created successfully.', 'success')
        return redirect(url_for('promo_manager'))
            
    promos = db.get_all_promos()
    return render_template('promos.html', promos=promos)

@app.route('/promos/delete/<code>', methods=['POST'])
@login_required
def delete_promo(code):
    db.delete_promo(code)
    flash(f'Promo code {code} deleted.', 'success')
    return redirect(url_for('promo_manager'))

@app.route('/feed')
@login_required
def feed_list():
    page = request.args.get('page', 1, type=int)
    limit = 10
    offset = (page - 1) * limit
    posts = db.get_wall_posts(offset=offset, limit=limit)
    total_items = db.get_wall_post_count()
    total_pages = (total_items + limit - 1) // limit
    return render_template('feed.html', posts=posts, page=page, total_pages=total_pages, total_items=total_items)

@app.route('/feed/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    db.delete_wall_post(post_id)
    flash(f'Post #{post_id} deleted successfully.', 'success')
    return redirect(request.referrer or url_for('feed_list'))

@app.route('/broadcast', methods=['GET', 'POST'])
@login_required
def broadcast():
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        schedule_time = request.form.get('schedule_time', '').strip()
        
        if not message:
            flash('Message cannot be empty.', 'error')
            return redirect(url_for('broadcast'))
            
        if schedule_time:
            # Handle scheduling
            try:
                # Expecting format: YYYY-MM-DDTHH:MM
                from datetime import datetime
                send_at = int(datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M').timestamp())
                if send_at < time.time():
                    flash('Scheduled time must be in the future.', 'error')
                    return redirect(url_for('broadcast'))
                    
                db.conn.execute("""
                    INSERT INTO scheduled_broadcasts (admin_id, message, send_at, status, created_at)
                    VALUES (?, ?, ?, 'pending', ?)
                """, (session.get('user_id', 0), message, send_at, int(time.time())))
                db.conn.commit()
                flash(f'Broadcast scheduled for {schedule_time}.', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Invalid date format: {e}', 'error')
                return redirect(url_for('broadcast'))

        # Immediate broadcast
        users = db.get_active_user_ids()
        
        success = 0
        failed = 0
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        for u_id in users:
            try:
                resp = requests.post(api_url, json={
                    'chat_id': u_id,
                    'text': f"📢 *Announcement*\n\n{message}",
                    'parse_mode': 'Markdown'
                }, timeout=2)
                if resp.status_code == 200:
                    success += 1
                else:
                    failed += 1
            except:
                failed += 1
                
        flash(f'Immediate broadcast complete. Sent to {success} users. Failed: {failed}.', 'info')
        return redirect(url_for('dashboard'))
        
    return render_template('broadcast.html')

@app.route('/reports')
@login_required
def report_list():
    page = request.args.get('page', 1, type=int)
    limit = 20
    offset = (page - 1) * limit
    reports = db.get_reports(status='pending', limit=limit, offset=offset)
    total_items = db.get_report_count(status='pending')
    total_pages = (total_items + limit - 1) // limit
    return render_template('reports.html', reports=reports, page=page, total_pages=total_pages, total_items=total_items)

@app.route('/reports/<action>/<int:report_id>', methods=['POST'])
@login_required
def report_action(action, report_id):
    c = db.conn.cursor()
    c.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()
    
    if not report:
        flash('Report not found.', 'error')
        return redirect(url_for('report_list'))
        
    if action == 'dismiss':
        db.resolve_report(report_id, 'dismissed')
        send_telegram_msg(report['reporter_id'], LANG['report_dismissed_notification'])
        flash(f'Report #{report_id} dismissed. Reporter notified.', 'success')
    elif action == 'ban':
        target_id = report['reported_id']
        db.ban_user(target_id, reason=f"Banned from Report #{report_id}: {report['reason']}")
        db.resolve_report(report_id, 'banned')
        
        # Notify Banned User 
        send_telegram_msg(target_id, LANG['ban_notification'])
        
        # Notify Reporters
        reporters = db.get_user_reporters(target_id)
        for rep_id in reporters:
            send_telegram_msg(rep_id, LANG['report_success_notification'])
            
        flash(f'User {target_id} banned and all associated reports resolved.', 'success')
        
    return redirect(url_for('report_list'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    if request.method == 'POST':
        for key, value in request.form.items():
            db.update_setting(key, value)
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('settings_page'))
        
    settings_dict = db.get_all_settings()
    settings = [{'key': k, 'value': v} for k, v in settings_dict.items()]
    return render_template('settings.html', settings=settings)

@app.route('/saved-chats')
@login_required
def saved_chats_list():
    page = request.args.get('page', 1, type=int)
    limit = 20
    offset = (page - 1) * limit
    chats = db.get_saved_chats_list(limit=limit, offset=offset)
    total_items = db.get_saved_chat_count()
    total_pages = (total_items + limit - 1) // limit
    return render_template('saved_chats.html', chats=chats, page=page, total_pages=total_pages, total_items=total_items)

@app.route('/saved-chats/view/<int:chat_id>/<int:user_id>')
@login_required
def view_saved_chat(chat_id, user_id):
    messages = db.get_saved_messages(chat_id, user_id)
    if not messages:
        flash('Saved chat not found.', 'error')
        return redirect(url_for('saved_chats_list'))
    return render_template('transcript.html', messages=messages, chat_id=chat_id, is_saved=True)

@app.route('/active-chats')
@login_required
def active_chats():
    chats = db.get_active_chats_detailed()
    return render_template('active_chats.html', chats=chats)

@app.route('/active-chats/stop/<int:chat_id>', methods=['POST'])
@login_required
def force_stop_chat(chat_id):
    chat = db.get_chat_by_id(chat_id)
    if chat:
        db.end_chat(chat_id)
        # Notify users
        send_telegram_msg(chat['user1_id'], "⚠️ *Notice:* This chat session has been terminated by administration.")
        send_telegram_msg(chat['user2_id'], "⚠️ *Notice:* This chat session has been terminated by administration.")
        flash(f'Chat #{chat_id} forcibly terminated.', 'success')
    return redirect(url_for('active_chats'))

@app.route('/reports/transcript/<int:chat_id>')
@login_required
def report_transcript(chat_id):
    messages = db.get_chat_history(chat_id)
    if not messages:
        flash('No chat history found for this report.', 'error')
        return redirect(url_for('report_list'))
    return render_template('transcript.html', messages=messages, chat_id=chat_id)

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)
