# confluence-tables
A module that enables interactions with tables in Confluence that are not available out of the box in the REST API.

# installation
Simply import the confluence_credentials module into your script. Either place the confluence-tables.py file in your python project's working directory, or in your PYTHONPATH directory, or append the directory to your system path.

# usage
You can pull all the tables from a Confluence page into a Pandas DataFrame by using the ingest_html method.
```
# Define variables
page_id = 377094384 # This is the PageId of the confluence page that we want to interact with. You can get this id from going to 'Page Information' in

confluence = ConfluenceTable(page_id)
df = confluence.ingest_html("dfs)
```

You can also update tables in a Confluence page by passing it a list of values that will comprise the rows of the table.
Things to note:
- The table must first exist in Confluence before you are able to update it with any values.
- Duplicates will not be added.
- If you pass a row with fewer values than the number of columns in Confluence, then blank columns will be inserted to fill the row.
- If you pass a row with more values the number of columns in Confluence, it will throw an error.

```
# Define variables
page_id = 377094384 # This is the PageId of the page that we want to update.
Confluence. The id is a number in the URL.
insert_list = [["Cathy Chatterly","Public Speaker"]] # This is the list of values we want to insert into the page.

# Create confluence object and update the table with the values.
confluence = ConfluenceTable(page_id,insert_list) # Here we pass the page id and the insert list to the ConfluenceTable class when we instantiate it.
confluence.update() # This runs the update of the page
```