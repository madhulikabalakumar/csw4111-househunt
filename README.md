# csw4111-househunt
by  
Gargi Patil (gp2723)  
Madhulika Balakumar (mb5144)  

### Setup
 **PostgreSQL Account Name:** csw4111-househunt  
 **Access UNI:**  mb5144  
 **URL:** http://104.196.56.92:8111/

### Features:

As proposed in Part 1, the following features are supported by the web application:


1. Browse house listings and rent _available_ houses after registering/logging in
2. A house cannot be rented by multiple people at the same time - so, you are allowed to only choose dates after the end of the existing lease end date
3. Filter and sort available houses based on attributes such as Number of Bedrooms, Number of Bathrooms, Price, Sq footage, Furnishing status, Availability dates, Elevator, Laundry, Safety Rating  
4. Allow renters to rate the safety of the house and the quality of entertainment around the building from their profile page for houses they have rented previously  
5. View a list of previous renters for any given house to understand the demographic suitability of the house. The following information is displayed: Pronouns, Citizenship, Degree Type, Family (true/false) and Designation


### Interesting Database Operations:  
The following webpages have interesting database operations:  

 **1. Interesting SQL Queries: Details and Profile pages**  
   The SQL queries for both these webpages use LEFT OUTER JOIN. For example:  

   student_details = conn.execute( "SELECT C.account_id, C.pronouns, S.degree_type, S.citizenship, G.score AS sscore, E.score AS escore FROM CU_User C, Student S, Lease_Info_Rented_By L LEFT OUTER JOIN Gave_Safety_Rating G ON L.account_id = G.account_id AND G.flat_no = L.flat_no AND G.bldg_address=L.bldg_address LEFT OUTER JOIN Gave_Entertainment_Rating E ON L.account_id = E.account_id AND E.bldg_address=L.bldg_address WHERE C.account_id = S.account_id AND L.account_id = S.account_id AND L.flat_no = %s AND L.bldg_address = %s", flat, bldg_name)

   The queries for Details webpage joins 3 tables and left outer joins on 2 tables to assimilate information stored across multiple tables. Similarly Profile webpage has a left outerjoin between 2 tables.  A left outer join is required as the user may not have rated safety/entertainment for the house.

 **2.  Interesting DB Workflow: Entertainment/Safety Reading in Profile page**  
   When a user rates the entertainment/safety of the listing, a new entry is made in the Gave_Entertainment_Rating/Gave_Safety_Rating table(s). The average rating is then calculated from the table(s) and the new rating is updated in Building/House_Belongs_To_Brokered_By table(s). The entertainment rating impacts all listings in that given building. 


### References used for HTML 
www.w3school.com  
(no AI tools were used)
