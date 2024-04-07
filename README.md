# confluence_tables
A module that enables interactions with tables in Confluence that are not available out of the box in the REST API.

# installation
Simply import the confluence_credentials module into your script. Either place the confluence-tables.py file in your python project's working directory, or in your PYTHONPATH directory or append the directory to your system path.

# usage
## pulling data from confluence into a dataframe
You can pull all the tables from a Confluence page into a Pandas DataFrame by using the ingest_html method.
```
import confluence_tables as ct

# Define variables
page_id = 377094384 # This is the PageId of the confluence page that we want to interact with. You can get this id from going to 'Page Information' in Confluence. The id is a number in the URL. We are just using '377094384' here as an example page_id.

c = ConfluenceTable(page_id)
df = ct.df # Pull our dataframe from the 'df' property of the 'ct' object.
```

## inserting data into a confluence page
You can also update tables in a Confluence page by passing it a list of values that will comprise the rows of the table.
Things to note:
- The table must first exist in Confluence before you are able to update it with any values.
- Duplicates will not be added.
- If you pass a row with fewer values than the number of columns in Confluence, then blank columns will be inserted to fill the row.
- If you pass a row with more values the number of columns in Confluence, it will throw an error.

```
page_id = 377094384 # This is the PageId of the page that we want to update.

c = ConfluenceTable(page_id)
insert_list = [["Cathy Chatterly","Public Speaker"],["Rod Handler","Nuclear Power Plant Worker"]] # This is the list of values we want to insert into the page.
ct.insert(insert_list) # This adds the rows in the insert list to the Confluence page.
```

## updating values in confluence
If we wanted to update a table in confluence, rather than inserting, then the process is to pull the data on the page into a dataframe, then remove the table from the 'html' property of the ConfluenceTable object using the clear_table() method. Next, we manipulate the data how we please using pandas. Lastly, we deploy our changes to the Confluence page. An example of this is below.
```
    c = ConfluenceTable(page_id)
    df = ct.df
    df = df.assign(Environment = "prod") # Set the values of the 'Environment' column in the dataframe to be 'prod'.
    insert_list = df.values.tolist() # Generate our list of values that we are going to insert.
    ct.clear_table() # Clear the table that is contained within the 'html' property of the 'ct' object.
    ct.insert(insert_list) # Deploy our updated table to Confluence using the insert() method.
```