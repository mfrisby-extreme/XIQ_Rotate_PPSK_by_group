import argparse
import logging
import getpass
import pandas as pd
from collections import defaultdict
import csv

from lib.xiq_api import XIQ, logger

############################################
###### User Variables
############################################
_XIQ_API_token = ''      # Enter XIQ auth bearer token
_pageSize = 10  # number of records to pull for each page (max 100)

_script_name = "Rotate_PPSK_by_group"
logger.setLevel(logging.INFO)






parser = argparse.ArgumentParser()
parser.add_argument('--external',action="store_true", help="Optional - adds External Account selection, to use an external VIQ")
parser.add_argument('--csv_file', default='user_password_list.csv', help='name of csv file to create')
args = parser.parse_args()

csv_file = args.csv_file

## XIQ API Setup
if _XIQ_API_token:
    x = XIQ(token=_XIQ_API_token)
else:
    print("Enter your XIQ login credentials")
    username = input("Email: ")
    password = getpass.getpass("Password: ")
    x = XIQ(user_name=username,password = password)
#OPTIONAL - use externally managed XIQ account
if args.external:
    accounts, viqName = x.selectManagedAccount()
    if accounts == 1:
        validResponse = False
        while validResponse != True:
            response = input("No External accounts found. Would you like to import data to your network?")
            if response == 'y':
                validResponse = True
            elif response =='n':
                logging.warning("script is exiting....\n")
                raise SystemExit
    elif accounts:
        validResponse = False
        while validResponse != True:
            print("\nWhich VIQ would you like to connect to?")
            accounts_df = pd.DataFrame(accounts)
            count = 0
            for df_id, viq_info in accounts_df.iterrows():
                print(f"   {df_id}. {viq_info['name']}")
                count = df_id
            print(f"   {count+1}. {viqName} (This is Your main account)\n")
            selection = input(f"Please enter 0 - {count+1}: ")
            try:
                selection = int(selection)
            except:
                logging.warning("Please enter a valid response!!")
                continue
            if 0 <= selection <= count+1:
                validResponse = True
                if selection != count+1:
                    newViqID = (accounts_df.loc[int(selection),'id'])
                    newViqName = (accounts_df.loc[int(selection),'name'])
                    x.switchAccount(newViqID, newViqName)


def main():

    print("*****************************************************************")
    print("Please select which type of user groups you want to select from")
    print("*****************************************************************")
    print("1 - Cloud PPSK Groups")
    print("2 - Local PPSK Groups")
    print("3 - All PPSK Groups")
    print("4 - ** Cancel and Quit **")
    print("\n")
    print("** Selecting an option will **NOT** regenerate any passwords, only retrieve the list of user groups **")
    valid_response_rx = False
    selection = None
    ppsk_type = None
    while not valid_response_rx:
        selection = input("Selection: ")
        print(f"selection={selection}")
        try:
            selection = int(selection)
        except:
            pass
        response_list = [1, 2, 3, 4]
        if selection not in response_list:
            print(f"ERROR: Sorry, {selection} is not a valid response.  Try again...")
            continue
        valid_response_rx = True
    if selection == 4:
        logging.info("Script has been canceled, exiting...")
        return
    elif selection == 3:
        logging.info("Retrieving ALL PPSK Groups")
        ppsk_type = None
    elif selection == 2:
        logging.info("Retrieving LOCAL PPSK Groups")
        ppsk_type = 'LOCAL'
    elif selection == 1:
        logging.info("Retrieving CLOUD PPSK Groups")
        ppsk_type = 'CLOUD'

    '''
    Get all the user groups from XIQ based on above input and build into a list of dictionary
    '''
    # logging.info("Retrieving all User Groups from XIQ")
    logging.info("Working...(page 1)")
    response = x.getUserGroups(page=1, limit=_pageSize, type=ppsk_type)
    logging.debug(f"Got Page 1 response: {response}")
    total_pages = response.get("total_pages", 1)
    group_list = response.get("data", [])

    if total_pages > 1:
        for pg in range(2, total_pages+1):
            logging.info(f"Working...(page {pg} of {total_pages})")
            response = x.getUserGroups(page=pg, limit=_pageSize, type=ppsk_type)
            logging.debug(f"Got Page {pg} response: {response}")
            group_list.extend(response.get("data", []))

    groups_dict = defaultdict(lambda: defaultdict(int))
    '''
    Build new dictionary keyed on a local id number
    '''
    local_id = 1
    for data_record in group_list:
        # print(type(data_record))
        groups_dict[local_id]["name"] = data_record.get("name")
        groups_dict[local_id]["id"] = data_record.get("id")
        groups_dict[local_id]["description"] = data_record.get("description")
        groups_dict[local_id]["password_db_location"] = data_record.get("password_db_location")
        local_id += 1

    '''
    Print menu for user selection of group
    '''
    row = 1
    print("********************************************************")
    print("Please make a selection from the following user groups")
    print("********************************************************")
    for id in groups_dict.keys():
        nm = groups_dict[id].get("name")
        xiq_id = groups_dict[id].get("id")
        print(f"{id} - {nm}")
    cancel_response = local_id  # should be the last local group id + 1
    print(f"{cancel_response} - ** Cancel and Quit **")
    print("\n")
    print("** Selecting an option will **NOT** regenerate any passwords, only retrieve the list users and their current passwords **")


    valid_response_rx = False
    selection = None
    while not valid_response_rx:
        selection = input("Selection: ")
        # print(f"selection={selection}")
        try:
            selection = int(selection)
        except:
            pass

        if selection == cancel_response:
            logging.info("User canceled, exiting...")
            return
        if selection not in groups_dict.keys():
            print(f"ERROR: Sorry, {selection} is not a valid response.  Try again...")
            continue
        valid_response_rx = True
        selected_name = groups_dict[selection].get("name")
        logging.info(f"User selected option \'{selection} - {selected_name}\'")

    '''
    Now we get all the users in the chosen usergroup
    '''
    usergroup_id = groups_dict[selection].get("id", 0)
    gp_name = groups_dict[selection]["name"]

    logging.info(f"Retrieving users for group {gp_name}")
    logging.info("Working...(page 1)")
    response = x.getUsersByGroupID(usergroup_id, page=1, limit=_pageSize)
    logging.debug(f"Got Page 1 response: {response}")
    total_pages = response.get("total_pages", 1)
    user_list = response.get("data", [])
    total_users = int(response.get("total_count"))
    if total_users == 0:
        logging.error(f"User group {gp_name} does not appear to have any users.  The script will now exit")
        return
    logging.info(f"There is a total of {total_users} records on {total_pages} pages")

    if total_pages > 1:
        for pg in range(2, total_pages + 1):
            logging.info(f"Working...(page {pg} of {total_pages})")
            response = x.getUsersByGroupID(usergroup_id, page=pg, limit=_pageSize)
            logging.debug(f"Got Page {pg} response: {response}")
            user_list.extend(response.get("data", []))

    '''
    build dictionary keyed on xiq id
    '''
    user_dict = defaultdict(lambda : defaultdict(int))
    for data_record in user_list:
        xiq_id = data_record.get("id")
        user_dict[xiq_id]["user_name"] = data_record.get("user_name")
        user_dict[xiq_id]["xiq_id"] = xiq_id
        user_dict[xiq_id]["existing_pw"] = data_record.get("password")
    print("***************************************************************")
    print("Please read the following carefully and then choose an option")
    print("***************************************************************")
    print("\n")
    print(f"There are {len(user_dict)} users in the group you have chosen.  By selecting proceed,\n"
          "the script will iterate through all of the users and generate new passwords.\n"
          "If email and/or SMS delivery notifications are enabled for the users, new notifications\n"
          "will be generated for each password change.\n"
          "\n"
          "\n"
          "Depending on the number of users in the group, the script may take several\n"
          "minutes or longer to complete"
          )

    print("1 - Proceed with password change")
    print("2 - Save current usernames/passwords to CSV and exit (new passwords will *NOT* be generated)")
    print("3 - Cancel and Quit")
    print("\n")

    valid_response_rx = False
    while not valid_response_rx:
        selection = input("Selection: ")
        print(f"selection={selection}")
        try:
            selection = int(selection)
        except:
            pass
        response_list = [1, 2, 3]
        if selection not in response_list:
            print(f"ERROR: Sorry, {selection} is not a valid response.  Try again...")
            continue
        valid_response_rx = True
    if selection == 3:
        logging.info("User has cancelled the script, exiting...")
        return
    elif selection == 2:
        logging.info(f"User selected option 2 - write current files to CSV ({csv_file})")
        field_names = [
            "xiq_id",
            "user_name",
            "existing_pw",
        ]
        logging.info(f"Writing to csv file - {csv_file}")

        with open(csv_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=field_names)

            # Write the header row
            writer.writeheader()

            # Write the data row
            for id ,user_record in user_dict.items():
                writer.writerow(user_record)

    elif selection == 1:
        logging.info("User selected option 3 - change all user passwords")
        print("******************************************")
        print("Are you sure you want to continue?\n"
              f"Typing 'yes' below will proceed with password regeneration for all {len(user_dict)} users! "
              )
        print("******************************************")

        valid_response_rx = False
        while not valid_response_rx:
            selection = input("Please type 'yes' or 'no': ")
            # print(f"selection={selection}")

            response_list = ['yes', 'no']
            if selection not in response_list:
                print(f"ERROR: Sorry, {selection} is not a valid response.  Please type yes or no to continue")
                continue
            valid_response_rx = True
        if selection == "no":
            return
        else:
            logging.info("Continuing with password regeneration")

            for xiq_user_id in user_dict.keys():
                usr = user_dict[xiq_user_id].get("user_name")
                logging.info(f"Changing PPSK key for user: {usr}")
                new_pw = x.postAPICall(f"/endusers/{xiq_user_id}/:regenerate-password")
                user_dict[xiq_user_id]["new_pw"] = new_pw.get("password")
                # print(f"NewPW={new_pw}")
            logging.info(f"Writing to csv file - {csv_file}")
            field_names = [
                "xiq_id",
                "user_name",
                "existing_pw",
                "new_pw",
            ]

            with open(csv_file, mode="w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=field_names)

                # Write the header row
                writer.writeheader()

                # Write the data row
                for id, user_record in user_dict.items():
                    writer.writerow(user_record)


    # print("Im done")

if __name__ == '__main__':
    main()
