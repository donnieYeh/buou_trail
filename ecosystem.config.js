module.exports = {
  apps: [
    {
      name: 'chua-okx-monitor',
      script: 'chua_ok_all.py',
      interpreter: 'python',
      args: '--config config.okx.json',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_restarts: 5,
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: '1'
      },
      error_file: 'log/pm2-error.log',
      out_file: 'log/pm2-out.log',
      merge_logs: true
    }
  ]
};
