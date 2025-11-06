"""
Zeabur部署Web服务入口
提供HTTP接口和内置定时任务调度器
"""
import os
import sys
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import threading

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main as run_main_task
from src.config import get_config

# 初始化Flask应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 任务状态
task_status = {
    'last_run': None,
    'last_success': None,
    'last_error': None,
    'is_running': False,
    'total_runs': 0,
    'success_runs': 0,
    'failed_runs': 0
}

# 任务锁
task_lock = threading.Lock()


def run_update_task():
    """执行IP更新任务"""
    global task_status
    
    # 检查是否已有任务在运行
    if task_status['is_running']:
        logger.warning("任务已在运行中,跳过本次执行")
        return
    
    with task_lock:
        task_status['is_running'] = True
        task_status['last_run'] = datetime.now().isoformat()
        task_status['total_runs'] += 1
    
    try:
        logger.info("=" * 60)
        logger.info("开始执行IP更新任务")
        logger.info("=" * 60)
        
        # 执行主任务
        exit_code = run_main_task()
        
        if exit_code == 0:
            task_status['success_runs'] += 1
            task_status['last_success'] = datetime.now().isoformat()
            task_status['last_error'] = None
            logger.info("✅ IP更新任务执行成功")
        else:
            task_status['failed_runs'] += 1
            task_status['last_error'] = f"任务退出码: {exit_code}"
            logger.error(f"❌ IP更新任务执行失败: 退出码 {exit_code}")
    
    except Exception as e:
        task_status['failed_runs'] += 1
        task_status['last_error'] = str(e)
        logger.error(f"❌ IP更新任务执行异常: {e}", exc_info=True)
    
    finally:
        task_status['is_running'] = False
        logger.info("=" * 60)


# 初始化定时任务调度器
scheduler = BackgroundScheduler(timezone='Asia/Shanghai')


def init_scheduler():
    """初始化定时任务"""
    try:
        # 从环境变量读取定时配置
        schedule_enabled = os.getenv('SCHEDULE_ENABLED', 'true').lower() == 'true'
        
        if not schedule_enabled:
            logger.info("定时任务已禁用")
            return
        
        # 默认每天3次: 8:00, 14:00, 20:00 (北京时间)
        schedule_times = os.getenv('SCHEDULE_TIMES', '8:00,14:00,20:00')
        
        for time_str in schedule_times.split(','):
            time_str = time_str.strip()
            try:
                hour, minute = map(int, time_str.split(':'))
                
                # 添加定时任务
                scheduler.add_job(
                    run_update_task,
                    CronTrigger(hour=hour, minute=minute),
                    id=f'update_task_{hour}_{minute}',
                    name=f'IP更新任务 {time_str}',
                    replace_existing=True
                )
                logger.info(f"✅ 已添加定时任务: 每天 {time_str} (北京时间)")
            
            except Exception as e:
                logger.error(f"❌ 添加定时任务失败 {time_str}: {e}")
        
        # 启动调度器
        scheduler.start()
        logger.info("🚀 定时任务调度器已启动")
        
        # 检查是否启动时立即执行一次
        run_on_startup = os.getenv('RUN_ON_STARTUP', 'false').lower() == 'true'
        if run_on_startup:
            logger.info("启动时立即执行一次任务...")
            threading.Thread(target=run_update_task, daemon=True).start()
    
    except Exception as e:
        logger.error(f"初始化定时任务失败: {e}", exc_info=True)


# ==================== API路由 ====================

@app.route('/')
def index():
    """首页 - 显示服务信息"""
    return jsonify({
        'service': 'Cloudflare优选IP自动更新服务',
        'status': 'running',
        'version': '2.0.0',
        'endpoints': {
            '/': '服务信息',
            '/health': '健康检查',
            '/status': '任务状态',
            '/trigger': '手动触发任务 (POST)',
            '/config': '配置信息'
        }
    })


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'scheduler_running': scheduler.running if scheduler else False
    })


@app.route('/status')
def status():
    """获取任务状态"""
    return jsonify({
        'task_status': task_status,
        'scheduler': {
            'running': scheduler.running if scheduler else False,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in scheduler.get_jobs()
            ] if scheduler else []
        }
    })


@app.route('/trigger', methods=['POST'])
def trigger():
    """手动触发任务"""
    # 可选: 添加简单的认证
    auth_token = request.headers.get('Authorization')
    expected_token = os.getenv('TRIGGER_TOKEN', '')
    
    if expected_token and auth_token != f'Bearer {expected_token}':
        return jsonify({
            'success': False,
            'error': '未授权访问'
        }), 401
    
    if task_status['is_running']:
        return jsonify({
            'success': False,
            'error': '任务已在运行中'
        }), 409
    
    # 在后台线程中执行任务
    threading.Thread(target=run_update_task, daemon=True).start()
    
    return jsonify({
        'success': True,
        'message': '任务已触发',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/config')
def config_info():
    """获取配置信息(不包含敏感信息)"""
    try:
        config = get_config()
        return jsonify({
            'filter_countries': config.filter_countries,
            'query_limit': config.query_limit,
            'max_latency': config.max_latency,
            'output_file': config.output_file,
            'cf_ray_enabled': config.cf_ray_detection_enabled,
            'github_repo': config.github_repo if config.github_repo else '未配置',
            'schedule_enabled': os.getenv('SCHEDULE_ENABLED', 'true'),
            'schedule_times': os.getenv('SCHEDULE_TIMES', '8:00,14:00,20:00')
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# ==================== 应用启动 ====================

if __name__ == '__main__':
    # 初始化定时任务
    init_scheduler()
    
    # 获取端口配置
    port = int(os.getenv('PORT', 8080))
    
    logger.info("=" * 60)
    logger.info("🚀 Cloudflare优选IP自动更新服务启动")
    logger.info(f"📡 监听端口: {port}")
    logger.info(f"⏰ 定时任务: {os.getenv('SCHEDULE_TIMES', '8:00,14:00,20:00')}")
    logger.info("=" * 60)
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )