import ftplib
import os
import shutil
import schedule
import time
import json
import random
import socket

working_dir = os.getcwd()


# check if folder exists, if not create it
def create_directory(directory_path):
    if os.path.exists(directory_path):
        print("Found " + directory_path + " directory...")
    else:
        print("Creating " + directory_path + " directory...")
        os.mkdir(directory_path)


# creating local directory to save downloaded files and the internal network folder to transfer the files
local_directory = "./FTP_Download"
internal_network = "./Internal_Network"
create_directory(local_directory)
create_directory(internal_network)


def save_file_record(file_data):
    while True:
        # if File_Transfer_History.json file exists, file_history will store the data on that file,
        # if not it will be an empty dictionary
        try:
            with open("File_Transfer_History.json", "r") as file:
                file_history = json.load(file)
        except FileNotFoundError:
            file_history = {}
        except json.decoder.JSONDecodeError:
            file_history = {}
        file_id = str((round(random.random() * 10000000000)))
        if "file" + file_id not in file_history:
            file_record = file_data
            file_history["file" + str(file_id)] = file_record
            with open("File_Transfer_History.json", "w") as file:
                json.dump(file_history, file)
                break


# this function will be called based on the scheduled time
def file_transfer_automation():

    os.chdir(working_dir)
    # check the contents on internal network and delete all the files in this folder
    # this will be executed at the start of this function execution in order to avoid accumulation
    # of a big number of files
    internal_files = os.listdir(internal_network)
    # delete all the files from the internal network
    for file in internal_files:
        try:
            os.remove(internal_network+"/"+file)
        except:
            print("Could not delete file: " + file)

    try:
        # connecting to the FTP server and downloading the file list
        # This server changes the password after some time, so if password is not working
        # we can use the new password from their site: https://dlptest.com/ftp-test/
        ftp = ftplib.FTP('ftp.dlptest.com')
        ftp.login("dlpuser", "rNrKYTX9g7z3RgJRmxWuGHbeu")
        print("Uploading test files to the FTP server...")
        # upload 5 test .txt files to the FTP server. This is to avoid cases when
        # there might be no available files on the FTP server
        for i in range(5):
            fp = open(f"Test{i}.txt", 'a+')
            ftp.storbinary('STOR %s' % os.path.basename(f"Test{i}.txt"), fp, 1024)
            fp.close()
            os.remove(f"Test{i}.txt")
        ftp.retrlines('LIST')
        file_list = ftp.nlst()
        # go to FTP_Download directory and loop through the files in FTP server to download them
        os.chdir(local_directory)
        for file in file_list:
            if str(file).endswith('.txt'):
                try:
                    with open(file, 'wb') as fp:
                        print("Downloading " + file)
                        ftp.retrbinary(f"RETR {file}", fp.write)
                        print("Finished downloading " + file)
                except ftplib.error_perm:
                    print("Could not download file " + file)
                except EOFError:
                    print("Connection terminated...")
                except:
                    print("Communication error from the server...")
        ftp.quit()
        # create a list with the local files
        local_files = os.listdir()
        print("The downloaded files are: ")
        for count, file in enumerate(local_files, 1):
            print(f"{count}. {file}")

        os.chdir("..")
        # loop through all the files on local folder and move all of them to the internal network
        for file in local_files:
            try:
                print("Moving " + file + " to internal network")
                shutil.move(local_directory + "/" + file, internal_network)
                print(f"{file} moved successfully")
                file_record = {
                    "status": "Success",
                    "message": "File was transferred successfully to the internal network",
                    "filename": file
                }
                save_file_record(file_record)
            except:
                print("There was a problem while transferring " + file + " to the internal network")
                file_record = {
                    "status": "Failure",
                    "message": "There was a problem while transferring the file to the internal network",
                    "filename": file
                }
                save_file_record(file_record)
    except socket.gaierror:
        print("An error occurred while connecting to the FTP server")
    except ftplib.error_perm:
        print("Could not login to the FTP server, Incorrect Credentials")
    except TimeoutError:
        print("Timeout error...")
    # except:
    #     print("There was a problem with the FTP connection...")


# setting a schedule to run the script
schedule.every().day.at("09:00").do(file_transfer_automation)

while True:
    schedule.run_pending()
    time.sleep(1)
