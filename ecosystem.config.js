module.exports = {
    apps: [
      {
        name: "flaskapp",
        script: "app.py",
        interpreter: "/home/ubuntu/right-ship-server/venv/bin/python3",
        env: {
          "PATH": "/home/ubuntu/right-ship-server/venv/bin"
        }
      }
    ]
  };