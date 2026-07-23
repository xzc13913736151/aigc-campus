# 启动 Django 后端：
conda activate aigc
python apps/api/manage.py runserver 0.0.0.0:8000
# 首次初始化数据库或需要恢复演示账号时，先执行：
python apps/api/manage.py migrate
D:\miniconda3\envs\aigc\python.exe apps/api/manage.py seed_demo_data
# 另开一个 PowerShell 窗口启动 H5 前端：
Set-Location F:\agents-learning\aigc-campus
cmd /c npx pnpm --dir apps/mp dev:h5
# Chrome 打开：
http://localhost:5173/
# 后端健康检查：
http://127.0.0.1:8000/health/