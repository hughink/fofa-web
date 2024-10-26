from flask import Flask, render_template, redirect, url_for, request, jsonify, Response, send_from_directory
import requests
import logging
import base64
import csv
import json
import os
from pathlib import Path
from forms import ConfigForm  # 导入表单类

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 设置密钥以支持表单

# 配置文件路径
CONFIG_FILE = os.path.join(Path.home(), 'config.json')
print(f"配置文件路径: {CONFIG_FILE}")

# 读取配置
def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

# 写入配置
def write_config(email, key):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'FOFA_EMAIL': email, 'FOFA_KEY': key}, f)

# 获取 FOFA 配置
config = read_config()
FOFA_EMAIL = config['FOFA_EMAIL'] if config else None
FOFA_KEY = config['FOFA_KEY'] if config else None

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    form = ConfigForm()
    if form.validate_on_submit():
        email = form.email.data
        key = form.key.data
        write_config(email, key)

        # 更新全局变量
        global FOFA_EMAIL, FOFA_KEY
        FOFA_EMAIL = email
        FOFA_KEY = key

        logger.debug("Redirecting to /fofa_search")  # 调试信息
        return redirect(url_for('fofa_search_page'))
    return render_template('configure.html', form=form)

def fofa_search(query, size):
    try:
        # 构建请求参数
        params = {
            'email': FOFA_EMAIL,
            'key': FOFA_KEY,
            'qbase64': base64.b64encode(query.encode()).decode(),
            'fields': 'ip,port,protocol,country_name,region,city,as_organization,host,domain,os,server,icp,title,jarm',
            'size': size,
        }

        # 发起请求
        response = requests.get('https://fofa.info/api/v1/search/all', params=params, verify=False)

        # 检查响应状态码
        if response.status_code != 200:
            logger.error(f"Error: Received status code {response.status_code}")
            return [], f"Error: Received status code {response.status_code}"

        # 解析响应内容
        data = response.json()
        if data.get('error'):
            logger.error(f"Error message from API: {data.get('errmsg')}")
            return [], f"Error: {data.get('errmsg')}"

        results = [{
            'ip': r[0], 'port': r[1], 'protocol': r[2], 'country_name': r[3],
            'region': r[4], 'city': r[5], 'as_organization': r[6],
            'host': r[7], 'domain': r[8], 'os': r[9], 'server': r[10],
            'icp': r[11], 'title': r[12], 'jarm': r[13]
        } for r in data['results']]

        return results, None  # 返回结果和无错误
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        return [], str(e)  # 返回空结果和错误信息

@app.route('/fofa_search', methods=['GET', 'POST'])
def fofa_search_page():
    global FOFA_EMAIL, FOFA_KEY  # 声明为全局变量以便修改
    if not FOFA_EMAIL or not FOFA_KEY:
        return redirect(url_for('configure'))  # 如果没有配置，重定向到配置页面

    results = []
    error_msg = None
    size = 20

    if request.method == 'POST':
        query = request.form.get('query')
        size = int(request.form.get('size', 20))

        if not query:
            error_msg = '请填写搜索查询。'
        else:
            results, error_msg = fofa_search(query, size)

    return render_template('fofa_search.html', results=results, error_msg=error_msg, size=size)

@app.route('/export_all', methods=['POST'])
def export_all():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['IP', 'Port', 'Protocol', 'Country', 'Region', 'City', 'Host', 'Domain', 'OS', 'Server', 'ICP',
                         'Title', 'JARM'])  # 写入表头
        for result in results:
            writer.writerow([
                result['ip'], result['port'], result['protocol'], result['country_name'],
                result['region'], result['city'], result['host'], result['domain'],
                result['os'], result['server'], result['icp'], result['title'], result['jarm']
            ])
        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=all_results.csv'})

@app.route('/export_ip', methods=['POST'])
def export_ip():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['IP'])  # 写入表头
        for result in results:
            writer.writerow([result['ip']])
        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=ip_results.csv'})

@app.route('/export_host', methods=['POST'])
def export_host():
    results = request.json.get('results')
    if not results:
        return jsonify({'error': '没有可导出的结果'}), 400

    def generate():
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Host'])  # 写入表头
        for result in results:
            writer.writerow([result['host']])
        output.seek(0)
        yield output.read()

    return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=host_results.csv'})

@app.route('/fofa_yf.html')
def serve_fofa_yufa():
    return send_from_directory('templates', 'fofa_yf.html')

@app.route('/css/style.css')
def style_css():
    return send_from_directory('templates/css', 'style.css')

@app.route('/js/script.js')
def script_js():
    return send_from_directory('templates/js', 'script.js')

@app.before_request
def check_config():
    global FOFA_EMAIL, FOFA_KEY  # 声明为全局变量以便修改
    if request.endpoint not in ['configure', 'static']:
        if not FOFA_EMAIL or not FOFA_KEY:
            return redirect(url_for('configure'))  # 如果没有配置，重定向到配置页面

if __name__ == '__main__':
    config = read_config()
    if not config or not config.get('FOFA_EMAIL') or not config.get('FOFA_KEY'):
        # 如果配置文件不存在或配置无效，启动后跳转到配置页面
        app.add_url_rule('/', 'home', lambda: redirect(url_for('configure')))
    else:
        # 如果配置存在且有效，启动后跳转到搜索页面
        app.add_url_rule('/', 'home', lambda: redirect(url_for('fofa_search_page')))

    app.run(debug=True)
