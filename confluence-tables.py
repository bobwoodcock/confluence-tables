import pandas as pd
import json
import requests
from requests.auth import HTTPBasicAuth
from copy import deepcopy
import confluence_credentials as cc # This should be a file that contains your credentials. Please see the confluence_credentials.py file for an example.

class ConfluenceUpdate:
    def __init__(self,page_id,insert_list=[[]]) -> None:
        self.page_id = page_id
        self.insert_list = insert_list
        self.auth = HTTPBasicAuth(cc.confluence_user, cc.confluence_password) # This is the username and password for the bot account that we are using to perform Confluence operations.
        self.html = self.ingest_html("html") # This is the HTML value of the ingested page, as a string.
        self.dfs = self.ingest_html("dfs") # This is a list of dataframes generated from the tables within the confluence page.
        self.df = self.dfs[0] # This is simply the first table in the list of generated dataframes.


    def update(self):
        """Running this method performs the whole update of the Confluence page."""
        html = deepcopy(self.html)

        for value in self.insert_list:
            html = self.add_row_to_html_table(value,html)

        status_code = self.update_page(html)
        if status_code == 200:
            print("Page updated succesfully.")
        else:
            print("Page update failed with status code: " + str(status_code))


    def url_from_page_id(self):
        """This generates the full url of the Needs Info page that we can then use to make requests to the REST API.
        
        Returns:
            url (string): This is the full URL that we can use to make requests to the REST API."""
        url = "https://%s/rest/api/content/%s?expand=body.view" % (cc.confluence_url,str(self.page_id))
        return url
    

    def ingest_html(self,output_type):
        """Makes an API request to confluence in order to get the html body of a page and extract the tables.
        
        Args:
        output_type (string): "dfs" or html". This determines whether we want to return a dataframe, or the html.
        
        Returns:
            dfs (list): A list of tables converted into dataframes contained within the html.
            OR
            html (html): the raw html of the page that we ingested."""

        
        # Make the curl GET request and store the response in a variable
        url = self.url_from_page_id()
        
        json_response = self.get_json_response(url)
        html = json_response["body"]["view"]["value"]
        dfs = pd.read_html(html)

        if output_type == "dfs":
            return dfs
        elif output_type == "html":
            return html
        else:
            print("Incorrect output type specified. Please use either 'dfs' or 'html'.")


    def get_json_response(self,url):
        """This function returns the json response from the Needs Info page.

        Args:
            url (string): the URL of the Confluence page that we want to retreive a JSON response from.
        
        Returns:
            json_response (json): the response from the Needs Info confluence page."""
        url = self.url_from_page_id()
        response = requests.get(url, auth=self.auth)
        json_response = response.json()

        return json_response
    
    
    def filter_incoming_row(self,row,empty_columns,row_length,total_columns):
        """Prevents duplicate rows from being inserted into the table.
        
        Args:
            row (list): the row that we checking to see if there's a duplicate.
            empty_columns (int): the number of empty columns.
            row_length (int): the number of incoming columns that we are going to compare to see if they already exist.
            total_columns (int): the total number of columns in the table in confluence.
            
        Returns:
            add_row (boolean): returns False if we a duplicate exists, and True if the incoming row doesn't already exist."""
        
        if empty_columns > 0:
            for i in range(empty_columns):
                row.append("")
        row = [row]

        incoming_df = pd.DataFrame(row,index=None,columns=self.df.columns.to_list())
     
        incoming_df = incoming_df.merge(self.df,how="left",indicator=True,on=incoming_df.columns.to_list()[:row_length])

        incoming_df = incoming_df[incoming_df["_merge"] == "left_only"]
        incoming_df = incoming_df.iloc[:,total_columns]

        if len(incoming_df.index) == 0:
            add_row = False
        else:
            add_row = True

        return add_row
    

    def table_row_html(self,row):
        """This takes a value and generates the HTML for the table row that would contain that value.
        
        Args:
            value (string): this is the value that will be in the generated HTML.
            row(list): the row values that will be inserted into the table. 
            
        Returns:
            tr (string): this is an HTML string that can be appended to the HTML for the Needs Info page."""
        
        tr = "<tr>\n"
        for value in row:
            tr += """<td colspan="1" class="confluenceTd">%s</td>\n"""  % value
        tr += "</tr>"

        return tr
    

    def add_row_to_html_table(self,row,html):
        """This adds an value as a new row to the table in the html supplied.
        
        Args:
            event (string): this is the event that will be added to the table in HTML.
            html: this is the html for the Needs Info page.
        
        Returns:
            html: the html with the added event."""
        
        html = str(html)

        col_count = len(self.df.columns)
        row_length = len(row)
        empty_columns = col_count - row_length

        add_row = self.filter_incoming_row(row,empty_columns,row_length,col_count)
        if add_row == True:            
            pos = html.rfind("</tbody>")
            tr = self.table_row_html(row)
            if pos > -1:
                html = html[:pos] + tr + html[pos:]
        
        return html
    
    
    def get_version(self):
        """This function determines the version number of the Confluence page.
        
        Returns:
            version (int): the current version number of the page."""
        
        url = "https://%s/rest/api/content/%s?expand=body.storage,version" % (cc.confluence_url,str(self.page_id))
        response = requests.get(url, auth=self.auth)
        json = response.json()

        version = json["version"]["number"]
        version = int(version)

        return version
    

    def get_title(self):
        """This function determines the title of the Confluence page.
        
        Returns:
            title (string): title of the page."""
        
        url = "https://%s/rest/api/content/%s?expand=body.storage,title" % (cc.confluence_url,str(self.page_id))
        response = requests.get(url, auth=self.auth)
        json = response.json()

        title = json["title"]

        return title
    

    def update_page(self,html):
        """This updates the Confluence page with the new html.

        Args:
            html: This is the updated html that we want to deploy to Confluence.
        
        Returns:
            response.status_code: This status code lets us know whether or not the PUT request we made to the Confluence REST API was successful."""

        url = "https://%s/rest/api/content/%s" % (cc.confluence_url,str(self.page_id))
        title = self.get_title()
        version_number = self.get_version() + 1
        payload = {
            'id': self.page_id,
            'type': 'page',
            'status': 'current',
            'title': title,
            "space":{"key":"JAV"},
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

        return response.status_code


def main():
    # insert_list = [["Cathy Chatterly","Public Speaker"]] # This is the list of values we want to insert into the page.
    # confluence = ConfluenceUpdate(377094384,insert_list)
    # confluence.update() # This runs the update of the page
    pass


if __name__ == "__main__":
    main()