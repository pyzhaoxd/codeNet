import paramiko
import pandas as pd
import jinja2
import os
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def connect_host(host, user, passwd):
    #print('- connecting host', 20 * '>')
    client.connect(host, username=user, password=passwd)

def close_host():
    #print('- closing host', 20*'>')
    client.close()

class ts:

    def __init__(self, host, user, passwd, sheet):

        self.host = host
        self.user = user
        self.passwd = passwd
        self.sheet = sheet

    def trouble_shoot(self):
        tsFile = 'ts_comm_mikrotik.xlsx'

        #command = {'Address infomation': 'ip add print',
        #           'Interfaces infomation': 'interface print detail terse'
        #           }
        #print('- reading file', 20 * '>')

        print('- Trouble Shooting '+ self.host, 20 * '>')

        if os.path.exists(tsFile):
            df = pd.read_excel(tsFile, sheet_name=self.sheet)
            df.dropna(inplace=True)
            fileCommand = df.set_index('Function').to_dict()['Command']
            #for k, v in command.items():
            for k, v in fileCommand.items():
                print('\n', 10 * '-', k, 10 * '-', '\n')
                self.send_command(v)
        else:
            print('- ERROR: Trouble Shoot File Does Not Exists!')
        close_host()
        print('- END' + self.host, 20 * '>')

    def send_command(self, command):
        connect_host(self.host, self.user, self.passwd)
        #print('- sending command', 20*'>')
        stdin, stdout, stderr = client.exec_command(command)
        for line in stdout:
            print(line.strip('\n'))

class config:

    def __init__(self, host, user, passwd, templateFile):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.templateFile = templateFile

    def render(self):
        confFile = 'mikrotik_config.xlsx'
        outFile = 'mikrotik_conf.rsc'

        if os.path.exists(confFile):
            df = pd.read_excel('mikrotik_config.xlsx', sheet_name='init')
            df.dropna(inplace=True)
            conf = df.set_index('Variable').to_dict()['Configuration']
        else:
            print('- ERROR: Configuration File Does Not Exists!')

        templateLoader = jinja2.FileSystemLoader(searchpath="./")
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(self.templateFile)
        output = template.render(conf=conf)
        print(output)

        if os.path.exists(outFile):
            os.remove(outFile)
            with open(outFile, "w+") as f:
               f.write(output)
        else:
            with open(outFile, "w+") as f:
               f.write(output)

    def send_conf(self):
        self.render()
        localFile = r'mikrotik_conf.rsc'
        remoteFile = '/mikrotik_conf.rsc'
        trans = paramiko.Transport((self.host, 22))
        trans.connect(username=self.user, password=self.passwd)
        sftp = paramiko.SFTPClient.from_transport(trans)
        print('- sending file', 20 * '>')
        sftp.put(localFile, remoteFile)
        print('- send successful!')
        trans.close()
        print('- import configuration', 20 * '>')
        connect_host(self.host,self.user,self.passwd)
        stdin, stdout, stderr = client.exec_command('import mikrotik_conf.rsc')
        for line in stdout:
            print(line.strip('\n'))
        close_host()

class backup:

    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd

    def bak_file(self):
        self.export_file()
        local_file = 'mikrotik_bak.rsc'
        remote_file = '/mikrotik_bak.rsc'
        trans = paramiko.Transport((self.host, 22))
        trans.connect(username=self.user, password=self.passwd)
        sftp = paramiko.SFTPClient.from_transport(trans)
        print('- Copying File', 20 * '>')
        sftp.get(remote_file, local_file)
        print('- Done!')
        trans.close()

    def export_file(self):
        connect_host(self.host,self.user,self.passwd)
        client.exec_command('export file=mikrotik_bak')
        print('- Generating Backup File', 20*'>')
        time.sleep(50)
        close_host()