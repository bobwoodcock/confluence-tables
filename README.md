# confluence_tables
A module that enables interactions with tables in Confluence that are not available out of the box in the REST API.

# Usage
## Ingest a table from Confluence
You can ingest all the tables from a confluence page. 
```
# Define variables
page_id = 123456789 # This is the PageId of the confluence page that we want to interact with. You can get this id from going to 'Page Information' in Confluence. The id is a number in the URL. We are just using '123456789' here as an example page_id.

ingest = Ingester(page_id)
df = ingest.df # Pull a dataframe from the 'df' property of the 'ingest' object. If there is more than one table, this is the first table.
dfs = ingest.dfs # Pull a list of tables from the Confluence page. This is useful if you have more than one table on the page.
```

## Update values in confluence
If we wanted to update a table in confluence, rather than inserting, then the process is to pull the data on the page into a list of dataframes using the Ingester object.

So for example:
```
page_id = 123456789
dfs = Ingester(page_id).dfs # Get the list of dataframes on the page.
```
Then, we manipulate the data in the list of dfs using pandas. When the data is ready to be uploaded to Confluence, we push it back up using the dfs_to_confluence method in the Updater class:
```
page_id = 123456789
update = Updater(page_id)
update.dfs_to_confluence(dfs) # Here was pass the list of dataframes that we have manipulated and want upload to confluence.
```

## Inserting data into a confluence page (deprecated, replacted by Updater object)
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