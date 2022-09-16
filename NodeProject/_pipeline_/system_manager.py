# -*- coding: utf-8 -*-
import json,os,pprint,sys,time,shutil
import datetime as dt

"""
Init
"""
root_path = os.path.dirname(os.path.abspath(__file__))
src_path = root_path+'/src'
site_package_path = root_path+'/src'+'/site-packages'

if not root_path in sys.path:
    sys.path.insert(0,root_path)
if not src_path in sys.path:
    sys.path.insert(0,src_path)
if not site_package_path in sys.path:
    sys.path.insert(0,site_package_path)
#Environment Linux
if not os.name == 'nt':
    sys.path.remove(site_package_path)

# Module
import pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
from gSheet import gSheet
gSheet.sheetName = 'Node Project Integration'
from notionDatabase import notionDatabase as ntdb

# Path
prev_dir = os.sep.join(root_path.split(os.sep)[:-1])
rec_dir = prev_dir + '/production_rec'
notiondb_dir = rec_dir + '/notionDatabase'

"""
Func
"""

def workspaceSetup(*_):
    path = os.sep.join(root_path.split(os.sep)[:-1]) #\project name
    workspaceJ = json.load(open(root_path + '/workspace.json', 'r'))
    for data in workspaceJ:
        name = data['name']
        makePath = path+'/{}'.format(name)
        if not os.path.isdir(makePath):
            os.makedirs(makePath)
            print('Create Dir {}'.format(makePath))

def versionBackup(extension, dirPath, dateFormat='%Y%m%d_%H%M%S'):
    if not '.' in extension:
        print('Skip backup version because [{}]'.format(extension))
        return None
    if not os.path.exists(dirPath):
        print('Skip backup version because path [{}]'.format(dirPath))
        return None
    for root, dirs, files in os.walk(dirPath, topdown=False):
        for name in files:
            filePath = os.path.join(root, name)
            if 'version' in filePath:
                continue
            if extension in filePath and not '.ini' in filePath:
                versionDir = root + '/version'
                mtime = os.stat(filePath).st_mtime
                dateStr = dt.datetime.fromtimestamp(mtime).strftime(dateFormat)
                new_fileName = name.replace(extension,'') + '_' + dateStr + extension
                new_filePath = root + os.sep + 'version' + os.sep + new_fileName
                if not os.path.exists(versionDir):
                    os.mkdir(versionDir)
                # print(maFilePath)
                if not os.path.exists(new_filePath) and not dateStr in name:
                    print('Backup {}'.format(new_filePath))
                    shutil.copyfile(filePath, new_filePath)

def load_worksheet(sheet, dir_path):
    data = gSheet.getAllDataS(sheet)
    save_path = dir_path + os.sep + sheet + '.json'
    json.dump(data, open(save_path, 'w'), indent=4)
    print('Load worksheet {} - {}'.format(gSheet.sheetName,sheet))

class integration:
    def init_notion_db(*_):
        load_worksheet('nt_database', rec_dir)
        db_path = rec_dir + '/nt_database.json'
        with open(db_path) as db_f:
            db_j = json.load(db_f)

        with open(ntdb.config_path) as r_config_f:
            r_config_j = json.load(r_config_f)
            r_config_j['database'] = db_j
        with open(ntdb.config_path, 'w') as w_config_f:
            json.dump(r_config_j, w_config_f,indent=4)

        ntdb.database = r_config_j['database']

    def load_notion_db(*_):
        if not os.path.exists(notiondb_dir):
            os.makedirs(notiondb_dir)
        ntdb.loadNotionDatabase(notiondb_dir)

    def notion_sheet(*_):
        base_path = os.sep.join(root_path.split(os.sep)[:-1]).replace('\\','/')
        nt_csv_dir = base_path + '/production_rec/notionDatabase/csv'
        csv_path_list = [nt_csv_dir + '/' + i for i in os.listdir(nt_csv_dir) if '.csv' in i]
        #print(csv_path_list)
        for csv_path in csv_path_list:
            sheet_dest_name = 'nt_{}'.format(csv_path.split('/')[-1].split('.')[0])
            print('upload destination sheet', sheet_dest_name)
            try:
                gSheet.updateFromCSV(csv_path, sheet_dest_name)
            except:
                print('can\'t upload dataframe to sheet {}'.format(sheet_dest_name))

class data:
    history_dir_name = '_history'

    def create_history(*_):
        for root, dirs, files in os.walk(rec_dir, topdown=False):
            for name in files:
                ext = '.csv'
                if not ext in name:
                    continue
                if data.history_dir_name in root:
                    continue
                file_path = os.path.join(root, name)

                hist_dir_path = os.path.join(root, data.history_dir_name)
                if not os.path.exists(hist_dir_path):
                    os.mkdir(hist_dir_path)

                mtime = os.stat(file_path).st_mtime
                mtime_hour = dt.datetime.fromtimestamp(mtime).hour
                mtime_srtftime = dt.datetime.fromtimestamp(mtime).strftime('%Y%m%d_00')
                if mtime_hour > 12:
                    mtime_srtftime = dt.datetime.fromtimestamp(mtime).strftime('%Y%m%d_01')

                hist_file_path = os.path.join(
                    hist_dir_path, name.replace(ext, '_{}{}'.format(mtime_srtftime, ext)))

                print('create history  ', hist_file_path.split(os.sep)[-1])
                shutil.copyfile(file_path, hist_file_path)

    def clear_past_history(*_):
        for root, dirs, files in os.walk(rec_dir, topdown=False):
            for name in files:
                ext = '.csv'
                if not ext in name:
                    continue
                if data.history_dir_name in root:
                    continue
                file_path = os.path.join(root, name)

                hist_dir_path = os.path.join(root, data.history_dir_name)
                name_no_ext = name.replace(ext,'')

                hist_file_list = sorted([ i for i in os.listdir(hist_dir_path) if name_no_ext in i ])

                file_limit = 5
                if len(hist_file_list) > file_limit:
                    del_file_list = hist_file_list[:-file_limit]
                    keep_file_list = hist_file_list[-file_limit:]
                    #print(del_file_list , keep_file_list)
                    del_path_list = [ os.path.join(hist_dir_path, i) for i in del_file_list ]
                    for i in del_path_list:
                        del_file = del_file_list[del_path_list.index(i)]
                        print('remove off-limit[{}] history files'.format(file_limit), del_file)
                        os.remove(i)

    def get_history_path_list(file_path):
        ext = '.csv'
        file_path = file_path.replace('/',os.sep)
        name = os.path.basename(file_path)
        name_no_ext = name.replace(ext,'')
        file_dir = os.path.dirname(file_path)
        hist_dir_path = file_dir + os.sep + data.history_dir_name
        hist_file_list = sorted([ i for i in os.listdir(hist_dir_path) if name_no_ext in i ])
        hist_path_list = [os.path.join(hist_dir_path, i) for i in hist_file_list]
        return hist_path_list

class error:
    file_path = rec_dir + '/main_traceback.csv'
    def record(text):
        try:
            data = {
                'date_time': dt.datetime.now().strftime('%m-%d-%Y %H:%M:%S'),
                'traceback' : str(text)
            }
            error.file_path = rec_dir + '/main_traceback.csv'

            df = pd.DataFrame()
            if os.path.exists(error.file_path):
                df = pd.read_csv(error.file_path)
            df = df.append(pd.DataFrame.from_records([data]))
            df.reset_index(inplace=True, drop=True)
            df.to_csv(error.file_path, index=False)
        except:
            pass

    def get_nortify(clear_after = True):
        if os.path.exists(error.file_path):
            df = pd.read_csv(error.file_path)
            df.drop_duplicates(['traceback'], inplace=True)
            rec = []
            for i in df.index.tolist():
                row = df.loc[i]
                rec.append(row.to_dict())
            if clear_after:
                os.remove(error.file_path)
            return rec
        else:
            return []

class fika: #teletubbies files
    def cache_layout_file():
        dir_path = r'C:\Fika\Projects\Dug\Shots\Publish'
        dest_dir_path = r'D:\GDrive\Temp\Fika\Works\Layout'

        for root, dirs, files in os.walk(dir_path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                dest_file_path = os.path.join(dest_dir_path, name)

                if not '_Layout.ma' in name:
                    continue

                is_exists = os.path.exists(dest_file_path)

                if not is_exists:
                    shutil.copyfile(file_path, dest_file_path)
                    print(file_path)
    """
    def cache_audio_file():
        dir_path = r'E:\Mocap'
        dest_dir_path = r'D:\GDrive\Temp\Fika\Works\Layout'

        for root, dirs, files in os.walk(dir_path, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                dest_file_path = os.path.join(dest_dir_path, name)

                if not 'Combined.wav' in name:
                    continue

                print(dirs,file_path)

                is_exists = os.path.exists(dest_file_path)

                if not is_exists:pass
                    #shutil.copyfile(file_path, dest_file_path)

    """


if __name__ == '__main__':
    #base_path = os.sep.join(root_path.split(os.sep)[:-1])
    #workspaceSetup()
    #versionBackup('.ma', base_path)
    integration.init_notion_db()
    integration.load_notion_db()
    integration.notion_sheet()
    #data.create_history()
    #data.clear_past_history()
    #print(data.get_history_path_list(r"D:\GDrive\Documents\2022\BRSAnimPipeline\work\NodeProject\NodeProject\production_rec\notionDatabase\csv\project.csv"))

    #fika.cache_layout_file()
    #fika.cache_audio_file()
    pass