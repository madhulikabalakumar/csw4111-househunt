# csw4111-househunt
by  
Gargi Patil (gp2723)  
Madhulika Balakumar (mb5144)  

### Setup
PostgreSQL account name: csw4111-househunt  
Access UNI:  mb5144  
URL:  

### Features:

As proposed in Part 1, the following features are supported by the web application:

1. Browse and book house listings
2. Filtering and sorting available houses based on
     * House attributes 
     * Building attributes
  
3. Allow renters to rate the safety of the house and the quality of entertainment around the building.
4. View a list of previous renters for any given house to understand the demographic suitability of the house. The following information is displayed: Pronouns, Citizenship, Degree Type, Family (true/false) and Designation


### Interesting Database Operations:  
The following webpages have interesting database operations:
1. Details and Profile pages  
   The SQL queries for both these webpages use LEFT OUTER JOIN as follows:

   student_details = conn.execute( "SELECT C.account_id, C.pronouns, S.degree_type, S.citizenship, G.score AS sscore, E.score AS escore FROM CU_User C, Student S, Lease_Info_Rented_By L LEFT OUTER JOIN Gave_Safety_Rating G ON L.account_id = G.account_id AND G.flat_no = L.flat_no AND G.bldg_address=L.bldg_address LEFT OUTER JOIN Gave_Entertainment_Rating E ON L.account_id = E.account_id AND E.bldg_address=L.bldg_address WHERE C.account_id = S.account_id AND L.account_id = S.account_id AND L.flat_no = %s AND L.bldg_address = %s", flat, bldg_name)

   The queries for Details webpage joins 3 tables and left outer joins on 2 tables to assimilate information stored across multiple tables. Similarly Profile webpage has a left outerjoin between 2 tables.  A left outer join is required as there may not always exist a safety/entertainment rating provided by the user for a house.

2. 
