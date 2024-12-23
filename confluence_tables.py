import pandas as pd
import json
import requests
from requests.auth import HTTPBasicAuth
from copy import deepcopy
from io import StringIO
from bs4 import BeautifulSoup
import confluence_credentials as cc # This should be a file that contains your credentials. Please see the confluence_credentials.py file for an example.

class ConfluenceTable:
    """Interacts with tables in Confluence. This is deprecated, and it is recommended that you use the Ingester and Updater classes."""
    def __init__(self, page_id) -> None:
        """
        Initializes a ConfluenceTable object.
        
        Args:
            page_id (int): the page_id of the Confluence page that we want to interact with.
            It will be an integer like 123456789.
        """
        self.page_id = page_id
        self.auth = HTTPBasicAuth(cc.confluence_user, cc.confluence_password) # This is the username and password for the bot account that we are using to perform Confluence operations.
        self.ingest_html()
        self.filter_override = False
        self.save_html = False

    def insert(self, insert_list=[[]]):
        """
        Inserts the list of rows to the table in the Confluence page.
        
        Args:
            insert_list (list): a list of rows to insert.
            Example: [["Cathy Chatterly", "Public Speaker"], ["Rod Handler", "Nuclear Power Plant Worker"]]
        """
        html = self.html.getvalue()
        for value in insert_list:
            html = self.add_row_to_html_table(value,html)
        self.deliver_payload(html)    

    def url_from_page_id(self):
        """
        Generates the full url of the Needs Info page that we can then use to make requests to the REST API.
        
        Returns:
            url (string): This is the full URL that we can use to make requests to the REST API.
        """
        url = "https://%s/rest/api/content/%s?expand=body.view" % (cc.confluence_url, str(self.page_id))
        return url

    def ingest_html(self):
        """
        Makes an API request to confluence in order to get the html body of a page and extract the tables.
        Sets object properties: html, df, dfs.
        """
        # Make the curl GET request and store the response in a variable
        url = self.url_from_page_id()
        json_response = self.get_json_response(url)
        html = json_response["body"]["view"]["value"]
        html = StringIO(str(html))
        dfs = pd.read_html(html)
        self.html = html # This is the HTML value of the ingested page, as a string.
        self.dfs = dfs # This is a list of dataframes generated from the tables within the confluence page.
        self.df = dfs[0] # This is simply the first table in the list of generated dataframes.

    def get_json_response(self, url):
        """
        Gets the JSON response from the supplied URL page.

        Args:
            url (string): the URL of the Confluence page that we want to retreive a JSON response from.
        
        Returns:
            json_response (json): the response from the Needs Info confluence page.
        """
        url = self.url_from_page_id()
        response = requests.get(url, auth=self.auth)
        json_response = response.json()
        return json_response
    
    def filter_incoming_row(self, row, empty_columns, row_length, total_columns):
        """
        Prevents duplicate rows from being inserted into the table.
        
        Args:
            row (list): the row that we checking to see if there's a duplicate.
            empty_columns (int): the number of empty columns.
            row_length (int): the number of incoming columns that we are going to compare to see if they already exist.
            total_columns (int): the total number of columns in the table in confluence.
            
        Returns:
            add_row (boolean): returns False if we a duplicate exists, and True if the incoming row doesn't already exist.
        """
        if empty_columns > 0:
            for i in range(empty_columns):
                row.append("")
        row = [row]
        incoming_df = pd.DataFrame(row,index=None,columns=self.df.columns.to_list())
        if self.df.shape[0] > 0:
            incoming_df = incoming_df.merge(self.df,how="left", indicator=True,on=incoming_df.columns.to_list()[:row_length])
            incoming_df = incoming_df[incoming_df["_merge"] == "left_only"]
            incoming_df = incoming_df.iloc[:,total_columns]

        if len(incoming_df.index) == 0:
            add_row = False
        else:
            add_row = True
        return add_row
    
    def table_row_html(self, row):
        """
        Takes a value and generates the HTML for the table row that would contain that value.
        
        Args:
            row (list): the row values that will be inserted into the table. 
            
        Returns:
            tr (string): this is an HTML string that can be appended to the HTML.
        """
        tr = "<tr>\n"
        for value in row:
            tr += """<td colspan="1" class="confluenceTd">%s</td>\n"""  % value
        tr += "</tr>"
        return tr
    
    def clear_table(self, deploy=False):
        """
        Clears the table in the html. If there is more than one table, it will clear the last table only.
        
        Args:
            deploy (boolean): Default is False. If true, then deploy the cleared table to the page in Confluence.
        """
        html = deepcopy(self.html)
        html = html.getvalue()
        html = html.replace(">",">\n")
        start_pos = html.rfind("</th>") + 5
        end_pos = html.rfind("</tbody>")
        html = html[:start_pos] + "</tr>" + html[end_pos:]
        html = StringIO(html)
        self.html = html
        self.df = self.df.iloc[0:0]
        if deploy==True:
            self.deliver_payload(html)
        
    def add_row_to_html_table(self, row, html):
        """
        Adds a value as a new row to the table in the html supplied.
        
        Args:
            row (string): this is the row that will be added to the table in HTML.
            html (html): this is the raw html.
        
        Returns:
            html (string): the html with the added event.
        """
        html = str(html)
        col_count = len(self.df.columns)
        row_length = len(row)
        empty_columns = col_count - row_length
        if self.filter_override == False:
            add_row = self.filter_incoming_row(row, empty_columns, row_length, col_count)
        else:
            add_row = True
        if add_row == True:            
            pos = html.rfind("</tbody>")
            tr = self.table_row_html(row)
            if pos > -1:
                html = html[:pos] + tr + html[pos:]
        return html
    
    def get_version(self):
        """
        Determines the version number of the Confluence page.
        
        Returns:
            version (int): the current version number of the page.
        """
        url = "https://%s/rest/api/content/%s?expand=body.storage,version" % (cc.confluence_url, str(self.page_id))
        response = requests.get(url, auth=self.auth)
        json = response.json()
        version = json["version"]["number"]
        version = int(version)
        return version
    
    def get_title(self):
        """
        Determines the title of the Confluence page.
        
        Returns:
            title (string): title of the page.
        """
        url = "https://%s/rest/api/content/%s?expand=body.storage,title" % (cc.confluence_url, str(self.page_id))
        response = requests.get(url, auth=self.auth)
        json = response.json()
        title = json["title"]
        return title
    
    def deliver_payload(self, html):
        """
        This updates the Confluence page with the new html.

        Args:
            html (string): This is the updated html that we want to deploy to Confluence.
        
        Returns:
            response.status_code (int): This status code lets us know whether or not the PUT request we made to the Confluence REST API was successful.
        """
        url = "https://%s/rest/api/content/%s" % (cc.confluence_url, str(self.page_id))
        title = self.get_title()
        version_number = self.get_version() + 1
        payload = {
            "id": self.page_id,
            "type": "page",
            "status": "current",
            "title": title,
            "space":{"key":cc.confluence_space},
            "body": {
                "storage": {
                    "value": html,
                    "representation" : "storage"
                }
            },
            "version":{"number":str(version_number)}
        }
        headers = {"Content-Type": "application/json"}
        response = requests.put(url, data=json.dumps(payload), headers=headers,auth=self.auth)
        if self.save_html == True:
            with open("confluence-table-saved.html", mode="w") as file:
                file.write(html)
        if response.status_code == 200:
            print("Page updated succesfully.")
        else:
            print("Page update failed with status code: " + str(response.status_code))
        return response.status_code

class Ingester(ConfluenceTable):
    """Used to ingest tables on Confluece pages."""
    def __init__(self, page_id) -> None:
        """Initializes an Ingester object."""
        super().__init__(page_id)

class Updater(ConfluenceTable):
    """Used to update tables on Confluence pages."""
    def __init__(self, page_id) -> None:
        """
        Initializes an Updater object.

        Args:
            page_id (int): the page_id of the confluence page.
            It will be a number like 123456789.
        """
        super().__init__(page_id)
    
    def dfs_to_confluence(self, dfs):
        """Replaces tables on the Confluence page with the supplied list of dataframes.
        
        Args:
            dfs (list of pandas.DataFrame): a list of dataframes that we will use to update the tables in the HTML.
        """
        original_html = self.html

        # Convert the dataframes to HTML tables
        dfs_html_tables = [df.to_html(index=False) for df in dfs]

        # Parse the original HTML content
        soup = BeautifulSoup(original_html, 'html.parser')
        
        # Find all the tables in the original HTML file
        original_tables = soup.find_all('table')
        
        # Ensure there are enough tables to replace
        if len(original_tables) != len(dfs_html_tables):
            raise ValueError(f"Number of tables in HTML ({len(original_tables)}) does not match number of dataframes ({len(dfs_html_tables)}).")
        
        # Replace the existing tables with the new ones from dfs_html_tables
        for i, table in enumerate(original_tables):
            new_table = BeautifulSoup(dfs_html_tables[i], 'html.parser').find('table')
            table.replace_with(new_table)

        # Deploy the updated HTML to Confluence.
        self.deliver_payload(str(soup))


def main():
    pass

if __name__ == "__main__":
    main()