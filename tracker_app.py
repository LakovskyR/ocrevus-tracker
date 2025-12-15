"""
PixelTracker - Email Open Tracking Server
Logs email opens when recipients load tracking pixels
"""

from flask import Flask, send_file, request
import io
import os
from datetime import datetime
import base64

app = Flask(__name__)

# 1x1 transparent PNG (base64)
PIXEL_DATA = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
)

# Log file
LOG_FILE = os.getenv('LOG_FILE', 'email_opens.log')

@app.route('/pixel/<tracking_id>.png')
def track_pixel(tracking_id):
    """
    Serve 1x1 transparent pixel and log the open
    tracking_id format: EMAIL_DATE_SECTOR_RECIPIENT
    Example: ocrevus_20251215_TERR013_thomas.gambade
    """
    
    # Extract metadata
    timestamp = datetime.now().isoformat()
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Log the open
    log_entry = f"{timestamp}|{tracking_id}|{ip}|{user_agent}\n"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error logging: {e}")
    
    # Return pixel
    return send_file(
        io.BytesIO(PIXEL_DATA),
        mimetype='image/png',
        as_attachment=False
    )

@app.route('/stats')
def view_stats():
    """View tracking statistics (protected in production)"""
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse logs
        opens = []
        for line in lines:
            parts = line.strip().split('|')
            if len(parts) >= 4:
                opens.append({
                    'timestamp': parts[0],
                    'tracking_id': parts[1],
                    'ip': parts[2],
                    'user_agent': parts[3]
                })
        
        # Basic stats
        total_opens = len(opens)
        unique_emails = len(set(o['tracking_id'] for o in opens))
        
        html = f"""
        <html>
        <head><title>Email Tracking Stats</title>
        <style>
            body {{font-family: Arial; padding: 20px; background: #f5f5f5;}}
            .stat {{background: white; padding: 20px; margin: 10px 0; border-radius: 8px;}}
            table {{width: 100%; border-collapse: collapse; margin-top: 20px;}}
            th, td {{padding: 10px; text-align: left; border-bottom: 1px solid #ddd;}}
            th {{background: #646db1; color: white;}}
            tr:hover {{background: #f5f5f5;}}
        </style>
        </head>
        <body>
        <h1>📊 Email Tracking Stats</h1>
        
        <div class="stat">
            <h2>Summary</h2>
            <p><strong>Total Opens:</strong> {total_opens}</p>
            <p><strong>Unique Emails:</strong> {unique_emails}</p>
            <p><strong>Open Rate:</strong> {(total_opens/unique_emails*100):.1f}% (avg opens per email)</p>
        </div>
        
        <div class="stat">
            <h2>Recent Opens</h2>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>Tracking ID</th>
                    <th>IP</th>
                    <th>User Agent</th>
                </tr>
        """
        
        # Show last 50 opens
        for open_event in reversed(opens[-50:]):
            html += f"""
                <tr>
                    <td>{open_event['timestamp'][:19]}</td>
                    <td>{open_event['tracking_id']}</td>
                    <td>{open_event['ip']}</td>
                    <td>{open_event['user_agent'][:80]}</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        </body>
        </html>
        """
        
        return html
        
    except FileNotFoundError:
        return "<h1>No tracking data yet</h1>", 404
    except Exception as e:
        return f"<h1>Error: {e}</h1>", 500

@app.route('/')
def home():
    """Health check"""
    return {
        'status': 'running',
        'service': 'Ocrevus Email Tracker',
        'version': '1.0'
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
