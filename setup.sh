ScriptPath=Null
ServicePath=/etc/systemd/system/github_backup.service

touch $ServicePath
cat > $ServicePath << EOF
[Unit]
Description=Github Backup
Wants=network.target
After=network.target

[Service]
WorkingDirectory=$(dirname "${ScriptPath}")
ExecStart=python3 $ScriptPath

[Install]
WantedBy=multi-user.target
EOF
echo "Service file Created"

systemctl create github_backup.service
systemctl start github_backup.service
echo "Service Created"

systemctl status github_backup.service