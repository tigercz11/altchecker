import sqlite3
from ftplib import FTP

def export_to_txt(db_file, txt_file):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Execute query to fetch data, sorted by Account_ID
    c.execute('''SELECT id, account_id, character_name, realm FROM characters ORDER BY account_id ASC''')
    data = c.fetchall()

    # Close connection to the database
    conn.close()

    # Write data to text file (excluding the header)
    with open(txt_file, 'w', encoding='utf-8') as f:
        for row in data:
            f.write(f"{row[0]},{row[1]},{row[2]},{row[3]}\n")

    print(f"Data exported to {txt_file} successfully.")

def upload_to_ftp(ftp_host, ftp_user, ftp_password, local_file, remote_dir):
    try:
        # Connect to FTP server
        ftp = FTP(ftp_host)
        ftp.login(user=ftp_user, passwd=ftp_password)

        # Change to the remote directory
        ftp.cwd(remote_dir)

        # Upload the local file to FTP
        with open(local_file, 'rb') as f:
            ftp.storbinary(f'STOR {local_file}', f)

        print(f"Uploaded {local_file} to FTP successfully.")

    except Exception as e:
        print(f"Error uploading file to FTP: {e}")

    finally:
        # Close FTP connection
        ftp.quit()

def main():
    db_file = 'blizzard_accounts.db'
    txt_file = 'blizzard_accounts.txt'
    export_to_txt(db_file, txt_file)

    # FTP credentials and upload settings
    ftp_host = ''
    ftp_user = ''
    ftp_password = ''
    remote_dir = '/'  # Change to the appropriate directory on the FTP server

    # Upload the text file to FTP
    upload_to_ftp(ftp_host, ftp_user, ftp_password, txt_file, remote_dir)

if __name__ == '__main__':
    main()
