# confluence-tables
A module that enables interactions with tables in Confluence that are not available out of the box in the REST API.

# installation
Drop the confluence-tables.py file in your PYTHONPATH directory.

# usage
    page_id = 377094384 # This is the PageId of the confluence page that we want to interact with. You can get this id from going to 'Page Information' in Confluence. The id is a number in the URL.
    insert_list = [["Cathy Chatterly","Public Speaker"]] # This is the list of values we want to insert into the page.
    confluence = ConfluenceTable(page_id,insert_list) # Here we pass the page id and the insert list to the ConfluenceTable class when we instantiate it.
    confluence.update() # This runs the update of the page