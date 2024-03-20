import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv


class DatabaseBackup:
    def __init__(self):
        load_dotenv()

        self.postgres_db_user = os.getenv('DB_USER')
        self.postgres_db_name = os.getenv('DB_NAME')
        self.backup_time = os.getenv('BACKUP_TIME')

        self.backup_directory = 'dumps'
        os.makedirs(self.backup_directory, exist_ok=True)

    def run_backup(self):
        current_time = datetime.now().strftime('%H:%M')
        if current_time == self.backup_time:
            current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M')
            dump_filename = f'backup_{current_datetime}.sql'
            dump_path = os.path.join(self.backup_directory, dump_filename)
            dump_command = f'pg_dump -U {self.postgres_db_user} -d {self.postgres_db_name} > {dump_path}'
            subprocess.run(dump_command, shell=True, check=True)
            print(f"The database has been successfully backed up to: {dump_path}")
        else:
            print(f"Database backup is not scheduled at the current time: {current_time}")


if __name__ == "__main__":
    db_backup = DatabaseBackup()
    db_backup.run_backup()
