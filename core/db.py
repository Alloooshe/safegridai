"""
    this file contains the DBManage class.
"""
import pymysql
import os 
from os.path import isfile,join
import numpy as np 
import pickle 
import socket

class DBManage:
    """class DBManage handles all operations that includes communication with database.
  
    Attributes:
        p_host (string) : database host name.
        port (int) : database server communication port.
        p_user (string) : database username.
        p_password (string) : connection password.
        p_db (string) : name of the database.
        m_mydb (obj) : database connection object.
    """
    
    def __init__(self):
        self.p_host='localhost'
        self.port = 3306
        self.p_user='root'
        self.p_password='*********'
        self.p_db='DBfaceapp'
        self.m_mydb=None

    def load_db(self):
        """
        creat connection to the database using the instance attributes.

        Returns
        -------
        None.

        """
        self.db_data_dict = []
        self.m_mydb = pymysql.connect(
            host = self.p_host,
            port=self.port,
            user = self.p_user,
            password = self.p_password,
            database = self.p_db
        )
        
        if self.m_mydb.open:
            print('Connected to MySQL database')

    def insert_db(self,tb_name,dict_vales) : 
        """insert into database, can handle any insert in any table.
        

        Parameters
        ----------
        tb_name : string
            table name inwhich to insert.
        dict_vales : dictionary
            containes the row values to insert, information are stored in the form "column name" : "column value".

        Returns
        -------
        None.

        """
        cursor = self.m_mydb.cursor()
        sql_query = 'INSERT INTO ' + tb_name
        col_name = ''
        lst = list(dict_vales.keys() ) 
        for i in range(0, len(lst) )  : 
            if i == len(lst) -1 : 
                col_name+= lst[i]
            else : 
                col_name+= lst[i] +','      
        col_name = ' ( ' + col_name +' ) VALUES ( '
        for i in range(0, len(lst ))  : 
            if i == len(lst) -1: 
                col_name+= '%s )'
            else : 
                col_name+='%s,'           
        sql_query+=col_name
        cursor.execute(sql_query,list(dict_vales.values()))
        self.m_mydb.commit()
       
    def get_suspect_image(self,susid) : 
        """
        get the image path of a suspect, the image would normally be in the knwon_people folder.

        Parameters
        ----------
        susid : string
            suspect id.

        Returns
        -------
        path : string
            path to suspect image.

        """
        cursor = self.m_mydb.cursor()
        sql_query='SELECT * FROM  suspect WHERE suspect_id = \''+susid+'\';'
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        path = ''
        for row in rows :
            lst =list(row)
            path =lst[3]                   
        return path
    
    def save_config(self,save_dir='configuration' ):
        """
        save database connection configuration to text file.

        Parameters
        ----------
        save_dir : string, optional
            configuration folder name. The default is 'configuration'.

        Returns
        -------
        None.

        """
        path = os.path.dirname(os.path.realpath(__file__))
        path=os.path.join(path,os.path.basename(save_dir))
        path=os.path.join(path,os.path.basename("db_connection.txt"))
        file = open(path,"w") 
        lines = "p_host :"+str(self.p_host)+"\n"
        lines += "p_user:"+str(self.p_user)+"\n"
        lines += "p_password:"+str(self.p_password)+"\n"
        lines += "p_db:"+str(self.p_db)+"\n"
        file.writelines(lines)
        file.close() 
        print('configuration was saved successfully ... ')
    
    def load_config (self,save_dir='configuration'):
        """
        loads database connection configuration.

        Parameters
        ----------
        save_dir : string, optional
            configuration folder name. The default is 'configuration'.

        Returns
        -------
        None.

        """
        path = os.path.dirname(os.path.realpath(__file__))
        path=os.path.join(path,os.path.basename(save_dir))
        path=os.path.join(path,os.path.basename("db_connection.txt"))
        file = open(path,"r") 
        lines = file.readlines()
        self.p_host = (lines[0].split(':')[1]).rstrip()
        self.p_user = (lines[1].split(':')[1]).rstrip()
        self.p_password =  (lines[2].split(':')[1]).rstrip()
        self.p_db= (lines[3].split(':')[1]).rstrip()
      
        file.close()
        print('configuration was loaded successfully .... ')
    
    def test_config(self,config_dict) :
        """
        test connection configuratiuon.

        Parameters
        ----------
        config_dict : dictionary
            contains the connection values which should be similar to the class db connection attributes.

        Returns
        -------
        bool
            is the connection configuration valid .
        str
            message.

        """
        try : 
            db = pymysql.connect(
                host = config_dict["p_host"],
                port=config_dict["port"],
                user = config_dict["p_user"],
                password = config_dict["p_password"],
                database = config_dict["p_db"]
            )
            if db.open:
                return True,'successfully connected to  database'
            return False,'failed to connect to the database'
        except :     
            return False,'failed to connect to the database'
    
    '''
    def read_trained_faces(self):
        """
        read all suspects information that is marked as trained, this means the suspects that the system should
        match against.

        Returns
        -------
        ret_emb : list
            list of embedding vectors of the suspects.
        ret_suspectid : list
            list of the suspects ids.

        """
        self.m_mydb = None
        self.load_db()
        cursor = self.m_mydb.cursor()
        sql_query= 'SELECT * FROM  suspect ;'
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        ret_emb = []
        ret_suspectid = []
        ret_is_trained=[]
        for row in rows :
            lst =list(row)
            arr =np.asarray(pickle.loads(lst[2]))
            ret_emb.append(arr)
            ret_suspectid.append(lst[1])
            ret_is_trained.append(lst[4])
        return ret_emb,ret_suspectid,ret_is_trained
    
    def add_trained_faces(self,folder_dir): 
        """
        handls db operation that corresponds to adding new suspect image to the known_people folder.
        the function ignores suspects which have been added previously, updates the trained flag in suspects table and
        add new row to openCV table.

        Parameters
        ----------
        folder_dir : string
            folder name.

        Returns
        -------
        None.

        """
        paths =[join(folder_dir,f) for f in  os.listdir(folder_dir) if  isfile( join(folder_dir,f) ) ]   
        _,old_ids,is_trained = self.read_trained_faces()
        ids=[]
        for i in range(0,len(old_ids)) : 
            if is_trained[i] == 'YES' : 
                ids.append(old_ids[i])
                
        for path in paths : 
            _,image_name =  os.path.split(path) 
            susid = image_name[:10]
            if susid not in ids: 
                ret =  self.change_training_status(susid)
                ret = self.update_suspect_image(susid,path)
                ret  = self.add_to_OpenCV(path)
                if ret : 
                    print('status on suspect '+str(susid)+' was updated')
        
       
        
    def change_training_status(self,susid) :
        """
        change suspect status to trained = YES. 

        Parameters
        ----------
        susid : string
            target suspect id.

        Returns
        -------
        bool
            True if successfull.

        """
        sql = "UPDATE suspect SET trained = \'YES\' WHERE suspect_id =\'"+susid+"\';"
        cursor = self.m_mydb.cursor()
        cursor.execute(sql)
        self.m_mydb.commit()
        return True 
    
    
    def add_to_OpenCV(self, path ) :
        """
        add new row to openCV table. build the value dictionary and uses self.insert_db to add a new row.

        Parameters
        ----------
        path : string
            suspect image path.

        Returns
        -------
        bool
            true if successfull.

        """
        _,image_name =  os.path.split(path) 
        susid = image_name[:10]
        time_stamp = image_name[11:30]
        short_path = os.path.join("known_people",os.path.basename(image_name))
        sound_path=os.path.join("sound",os.path.basename("sparcle.wav"))
        ip =self.get_ip()
        dic = {"suspect_id" : susid , "suspect_name" : "NA" , "reports" : "NA" , "identified_by" : ip,"video_feed_location": "NA",
                 "detection_time_date" : time_stamp,"sound_file" : sound_path,"alarm_status" : 0,"alarm_reset_minutes" : 20 ,
                 "wifi_ip" : "NA" , "person_of_interest_image" :short_path, "person_of_interest_name" : "", "ip_address" : ip,
                 "privacy_settings"  : 0
                 
                 }
        self.insert_db("openCV",dic)
        return True
         
         
    def update_suspect_image(self,susid, path) :
        """
        update the value of the image_path column in suspect table.

        Parameters
        ----------
        susid : string
            target suspect id.
        path : string
            new image path.

        Returns
        -------
        bool
            true if successfull.

        """
        sql = "UPDATE suspect SET image_path = \'"+path+"\' WHERE suspect_id =\'"+susid+"\';"
        cursor = self.m_mydb.cursor()
        cursor.execute(sql)
        self.m_mydb.commit()
        return True 
    
    
    def update_users_status(self) : 
        """
        updates users alarm status to 1.

        Returns
        -------
        bool
            true of successsfull.

        """
        cursor = self.m_mydb.cursor()
        sql ="SET SQL_SAFE_UPDATES = 0;"
        cursor.execute(sql)
        sql = "UPDATE sub_users SET alarm_status= 1 WHERE true; "
        sql ="SET SQL_SAFE_UPDATES = 1;"
        cursor.execute(sql)      
        self.m_mydb.commit()
        return True  

    def get_ip(self):
        """
        get the current device ip.

        Returns
        -------
        IP : string
            device ip.

        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
          s.connect(('10.255.255.255', 1))
          IP = s.getsockname()[0]
        except:
          IP = '127.0.0.1'
        finally:
          s.close()
        return IP   
        
     '''   