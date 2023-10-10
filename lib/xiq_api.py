import logging
import os
import inspect
import sys
import json
import requests
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from requests.exceptions import HTTPError
from lib.logger import CustomLogger
custom_logger = CustomLogger()
logger = custom_logger.create_logger()

PATH = current_dir

class XIQ:
    def __init__(self, user_name=None, password=None, token=None):
        self.URL = "https://api.extremecloudiq.com"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.totalretries = 5
        self.locationTree_df = pd.DataFrame(columns = ['id', 'name', 'type', 'parent'])
        if token:
            self.headers["Authorization"] = "Bearer " + token
        else:
            try:
                self.__getAccessToken(user_name, password)
            except ValueError as e:
                logging.error(e)
                raise SystemExit
            except HTTPError as e:
               logging.error(e)
               raise SystemExit
            except:
                log_msg = "Unknown Error: Failed to generate token for XIQ"
                logger.error(log_msg)
                raise SystemExit
    #API CALLS
    def __setup_get_api_call(self, info, url):
        success = 0
        for count in range(1, self.totalretries):
            try:
                response = self.__get_api_call(url=url)
            except ValueError as e:
                logging.warning(f"API to {info} failed attempt {count} of {self.totalretries} with {e}")
            except Exception as e:
                logging.error(f"API to {info} failed with {e}")
                logging.info('script is exiting...')
                raise SystemExit
            except:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with unknown API error")
            else:
                success = 1
                break
        if success != 1:
            logging.error("failed to {}. Cannot continue to import".format(info))
            logging.info("exiting script...")
            raise SystemExit
        if 'error' in response:
            if response['error_mssage']:
                log_msg = (f"Status Code {response['error_id']}: {response['error_message']}")
                logger.error(log_msg)
                logging.error(f"API Failed {info} with reason: {log_msg}")
                logging.info("Script is exiting...")
                raise SystemExit
        return response
        
    def __setup_post_api_call(self, info, url, payload):
        success = 0
        for count in range(1, self.totalretries):
            try:
                response = self.__post_api_call(url=url, payload=payload)
            except ValueError as e:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with {e}")
            except Exception as e:
                logging.error(f"API to {info} failed with {e}")
                logging.info('script is exiting...')
                raise SystemExit
            except:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with unknown API error")
            else:
                success = 1
                break
        if success != 1:
            logging.error("failed {}. Cannot continue to import".format(info))
            logging.info("exiting script...")
            raise SystemExit
        if 'error' in response:
            if response['error_mssage']:
                log_msg = (f"Status Code {response['error_id']}: {response['error_message']}")
                logger.error(log_msg)
                logging.error(f"API Failed {info} with reason: {log_msg}")
                logging.info("Script is exiting...")
                raise SystemExit
        return response
    
    def __setup_put_api_call(self, info, url, payload=''):
        success = 0
        for count in range(1, self.totalretries):
            try:
                if payload:
                    self.__put_api_call(url=url, payload=payload)
                else:
                    self.__put_api_call(url=url)
            except ValueError as e:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with {e}")
            except Exception as e:
                logging.error(f"API to {info} failed with {e}")
                logging.info('script is exiting...')
                raise SystemExit
            except:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with unknown API error")
            else:
                success = 1
                break
        if success != 1:
            logging.error("failed to {}. Cannot continue to import".format(info))
            logging.info("exiting script...")
            raise SystemExit
        
        return 'Success'


    def __get_api_call(self, url):
        try:
            response = requests.get(url, headers= self.headers)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise ValueError(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise ValueError(log_msg)
        if response.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                    raise ValueError(log_msg)
            raise ValueError(log_msg) 
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
            raise ValueError("Unable to parse the data from json, script cannot proceed")
        return data

    def __post_api_call(self, url, payload):
        try:
            response = requests.post(url, headers= self.headers, data=payload)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise ValueError(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise ValueError(log_msg)
        if response.status_code == 202:
            return "Success"
        elif response.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text()}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                    raise Exception(data['error_message'])
            raise ValueError(log_msg)
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(response.status_code)}")
            raise ValueError("Unable to parse the data from json, script cannot proceed")
        return data
    
    def __put_api_call(self, url, payload=''):
        try:
            if payload:
                response = requests.put(url, headers= self.headers, data=payload)
            else:
                response = requests.put(url, headers= self.headers)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise ValueError(f'HTTP error occurred: {http_err}') 
        if response is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise ValueError(log_msg)
        if response.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{response.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                    raise Exception(data['error_message'])
                else:
                    logger.warning(data)
                raise ValueError(log_msg)
        return response.status_code

    def __getAccessToken(self, user_name, password):
        info = "get XIQ token"
        success = 0
        url = self.URL + "/login"
        payload = json.dumps({"username": user_name, "password": password})
        for count in range(1, self.totalretries):
            try:
                data = self.__post_api_call(url=url,payload=payload)
            except ValueError as e:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with {e}")
            except Exception as e:
                logging.error(f"API to {info} failed with {e}")
                logging.info('script is exiting...')
                raise SystemExit
            except:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with unknown API error")
            else:
                success = 1
                break
        if success != 1:
            logging.error("failed to get XIQ token. Cannot continue to import")
            logging.info("exiting script...")
            raise SystemExit
        
        if "access_token" in data:
            #print("Logged in and Got access token: " + data["access_token"])
            self.headers["Authorization"] = "Bearer " + data["access_token"]
            return 0

        else:
            log_msg = "Unknown Error: Unable to gain access token for XIQ"
            logger.warning(log_msg)
            raise ValueError(log_msg)

    ## EXTERNAL FUNCTION

    # EXTERNAL ACCOUNTS
    def __getVIQInfo(self):
        info="get current VIQ name"
        success = 0
        url = "{}/account/home".format(self.URL)
        for count in range(1, self.totalretries):
            try:
                data = self.__get_api_call(url=url)
            except ValueError as e:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with {e}")
            except:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with unknown API error")
            else:
                success = 1
                break
        if success != 1:
            logging.error(f"Failed to {info}")
            return 1
            
        else:
            self.viqName = data['name']
            self.viqID = data['id']
            
    #ACCOUNT SWITCH
    def selectManagedAccount(self):
        self.__getVIQInfo()
        info="gather accessible external XIQ acccounts"
        success = 0
        url = "{}/account/external".format(self.URL)
        for count in range(1, self.totalretries):
            try:
                data = self.__get_api_call(url=url)
            except ValueError as e:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with {e}")
            except:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with unknown API error")
            else:
                success = 1
                break
        if success != 1:
            logging.error(f"Failed to {info}")
            return 1
            
        else:
            return(data, self.viqName)


    def switchAccount(self, viqID, viqName):
        info=f"switch to external account {viqName}"
        success = 0
        url = "{}/account/:switch?id={}".format(self.URL,viqID)
        payload = ''
        for count in range(1, self.totalretries):
            try:
                data = self.__post_api_call(url=url, payload=payload)
            except ValueError as e:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with {e}")
            except Exception as e:
                logging.error(f"API to {info} failed with {e}")
                logging.info('script is exiting...')
                raise SystemExit
            except:
                logging.error(f"API to {info} failed attempt {count} of {self.totalretries} with unknown API error")
            else:
                success = 1
                break
        if success != 1:
            logging.error("failed to get XIQ token to {}. Cannot continue to import".format(info))
            logging.info("exiting script...")
            raise SystemExit
        
        if "access_token" in data:
            #print("Logged in and Got access token: " + data["access_token"])
            self.headers["Authorization"] = "Bearer " + data["access_token"]
            self.__getVIQInfo()
            if viqName != self.viqName:
                logger.error(f"Failed to switch external accounts. Script attempted to switch to {viqName} but is still in {self.viqName}")
                # print("Failed to switch to external account!!")
                logging.info("Script is exiting...")
                raise SystemExit
            return 0

        else:
            log_msg = "Unknown Error: Unable to gain access token for XIQ"
            logger.warning(log_msg)
            raise ValueError(log_msg) 

    def checkApsBySerial(self, listOfSerials):
        info="check APs by Serial Number"
        url = self.URL + "/devices?limit=100&sns="
        snurl = "&sns=".join(listOfSerials)
        url = url + snurl
        response = self.__setup_get_api_call(info, url)
        return(response['data'])

    def onboardAps(self, data):
        info="onboard APs"
        url = "{}/devices/:onboard".format(self.URL)
        payload = json.dumps(data)
        response = self.__setup_post_api_call(info,url,payload)
        return response

    def getUserGroups(self, page=1, limit=10, type=None):
        response = ""

        if type is None:
            type_str = ""
        else:
            type_str = "&" + "password_db_location=" + str.upper(type)

        info="Get User Groups"
        url = self.URL + f"/usergroups?page={page}&limit={limit}{type_str}"
        response = self.__setup_get_api_call(info, url)
        return response

    def getUsersByGroupID(self, group_id, page=1, limit=10):
        response = ""
        info = "Get Users by Group ID"
        url = self.URL + f"/endusers?page={page}&limit={limit}&user_group_ids={group_id}"
        response = self.__setup_get_api_call(info, url)
        return response

    def getRadioProfiles(self, page=1, limit=10):
        info = "Get Radio Profiles"
        # page = 1
        # limit = 100
        url = self.URL + f"/radio-profiles?page={page}&limit={limit}"
        response = self.__setup_get_api_call(info, url)
        return response

    def getRPChannelSelection(self, id):
        info = "Get Radio Profile Channel Selection"
        url = self.URL + f"/radio-profiles/channel-selection/{id}"
        response = self.__setup_get_api_call(info, url)
        return response

    def getRPRadioUsageOpt(self, id):
        info = "Get Radio Profile Radio Usage Optimization"
        url = self.URL + f"/radio-profiles/radio-usage-opt/{id}"
        response = self.__setup_get_api_call(info, url)
        return response
    def postAPICall(self, url, payload=None, info=None):
        url = self.URL + url
        return self.__setup_post_api_call(info, url, payload)
