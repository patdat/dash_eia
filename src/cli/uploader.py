import oss2
import pandas as pd
from io import StringIO

ali_bucket = 'pcia-crude'
ali_server = 'oss-us-east-1.aliyuncs.com'
ali_access_key_id = 'LTAI5t6VaDLAiK1J4zb3S4U5'
ali_secret_access_key = '97OvykD3LgoKvxakEoDgvWNp5MK8Bl'

class ali:
    """
    A class for uploading a DataFrame to Aliyun OSS (Object Storage Service).

    Parameters:
    df (pd.DataFrame): The DataFrame to be uploaded.
    dir_name (str): The directory name in OSS where the file will be stored.
    filename (str): The name of the file in OSS.
    df_index (bool, optional): If True, include the DataFrame index in the uploaded data.

    Attributes:
    shared_link (str): The shared link to the uploaded file in OSS.
    """
    def __init__(self, df,dir_name,filename,df_index=True):
        self.server = ali_server
        self.bucket_name = ali_bucket
        self.access_key_id = ali_access_key_id
        self.access_key_secret = ali_secret_access_key
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(self.auth, f'https://{self.server}', self.bucket_name, is_cname=False)
        self.upload_dataframe(df, dir_name, filename, df_index)

    def upload_dataframe(self, df, dir_name, filename, df_index):
        # Create a CSV buffer to store the DataFrame as CSV data
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=df_index)

        # Upload the CSV data to Aliyun OSS
        object_path = f'{dir_name}/{filename}'
        self.bucket.put_object(object_path, csv_buffer.getvalue().encode())

        # Generate the shared link for the uploaded file
        self.shared_link = f'https://{self.bucket_name}.{self.server}/{object_path}'
        
        # return shared_link

    def __repr__(self):
         return f'ALI: {self.shared_link}'
               
if __name__ == '__main__':
    import numpy as np
    df = pd.DataFrame(np.random.randint(0,100,size=(100, 4)), columns=list('ABCD'))
    ali(df,'TEST','test.csv',df_index=False)    
    
def cloud(df, filePath,fileName,df_index=True):
    """
    Args:
        df (pd.DataFrame): The DataFrame to be uploaded.
        filePath (str): The directory path where the file will be stored.
        fileName (str): The name of the file.
        df_index (bool, optional): If True, include the DataFrame index in the uploaded data.
    """
    ali_uploader = ali(df, filePath,fileName,df_index)
    print(repr(ali_uploader))    