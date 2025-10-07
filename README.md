'''
cd ~/Desktop/AI_Projects/MenaDevs_Assessment/GenAI_Assessment
python -m db.seed

'''

-----------------------------------
find_book
{ "query": "Find books by Robert C. Martin" }
---------------------------

restock_book
{
  "query": "Restock Clean Code book by 45"
}
--------------------------------------
 
create_order

simple order
{
  "query": "Create an order for customer 2 for 2 copies of Clean Code"
}

hard order(book name and isbn not exist in seeds)
{
  "query": "Create an order for customer 2 for 2 copies of Clean Code and 1 copy of Refactoring"
}
-----------------------------

update_price
{ "query": "Update the price of Clean Code to 50 dollars" }
----------------------------------------------

order_status
{ "query": "What is the status of order 2?" }
-----------------------------------------


inventory_summary
{ "query": "Show me all books that are running low on stock" }
----------------------------------------------------------
