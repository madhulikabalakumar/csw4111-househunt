# csw4111-househunt
by  
Gargi Patil (gp2723)  
Madhulika Balakumar (mb5144)  

### Setup
 **PostgreSQL Account Name:** csw4111-househunt  
 **Access UNI:**  mb5144  
 **URL:** http://104.196.56.92:6111/
 (any port between 8000 to 9000 or 6111 works)

### Features:

As proposed in Part 1, the following features are supported by the web application:


1. Browse house listings and rent _available_ houses after registering/logging in
2. A house cannot be rented by multiple people at the same time - so, you are allowed to only choose dates after the end of the existing lease end date
3. Filter and sort available houses based on attributes such as Number of Bedrooms, Number of Bathrooms, Price, Sq footage, Furnishing status, Availability dates, Elevator, Laundry, Safety Rating  
4. Allow renters to rate the safety of the house and the quality of entertainment around the building from their profile page for houses they have rented previously  
5. View a list of previous renters for any given house to understand the demographic suitability of the house. The following information is displayed: Pronouns, Citizenship, Degree Type, Family (true/false) and Designation


### Interesting Database Operations:  
The following webpages have interesting database operations:  

  **1. Profile Page:**  
  The profile page provides a detailed view of the user's information, including personal details, past rented houses, and the ability to rate safety and entertainment.

  Database Operations:  
  User Information Retrieval:  
  A query retrieves user-specific information by joining the CU_User, Student, and Lease_Info_Rented_By tables.  
  A LEFT OUTER JOIN is used with Gave_Safety_Rating and Gave_Entertainment_Rating to include safety and entertainment ratings, even if the user has not rated them.  
  For example:  
    student_details = conn.execute( "SELECT C.account_id, C.pronouns, S.degree_type, S.citizenship, G.score AS sscore, E.score AS escore FROM CU_User C, Student S, Lease_Info_Rented_By L LEFT OUTER JOIN Gave_Safety_Rating G ON L.account_id = G.account_id AND G.flat_no = L.flat_no AND G.bldg_address=L.bldg_address LEFT OUTER JOIN Gave_Entertainment_Rating E ON L.account_id = E.account_id AND E.bldg_address=L.bldg_address WHERE C.account_id = S.account_id AND L.account_id = S.account_id AND L.flat_no = %s AND L.bldg_address = %s", flat, bldg_name)  

  Safety and Entertainment Ratings:  
  Conditional checks are made to determine if the user has previously rated safety and entertainment for a specific leased house.
  If the user has not rated, a form is displayed to input new ratings.  
  Upon submitting the form, new entries are created in the Gave_Safety_Rating or Gave_Entertainment_Rating table.  

  Dynamic Content Display:  
  The retrieved information is dynamically displayed on the profile page, allowing the user to view their details and past leases.  

  Why it's Interesting:  
  The dynamic nature of the page, displaying user-specific information and accommodating user ratings, requires intricate database queries.  
  The use of LEFT OUTER JOIN ensures that even if a user hasn't provided ratings, their information is still displayed.  

  **2. Details Page:**   
  The details page provides comprehensive information about a specific house, including amenities, user ratings, broker details, and previous renters.  

  Database Operations:  
  House Information Retrieval:  
  Queries retrieve detailed information about the selected house by joining the House_Belongs_To_Brokered_By, Building, Gave_Safety_Rating, and Gave_Entertainment_Rating tables.  
  The information is displayed based on the house and building details.  

  User Ratings and Broker Information:  
  Similar to the profile page, conditional checks are made to determine if users have previously rated safety and entertainment for this house.  
  Broker information is retrieved and displayed based on the house and building details.  

  Previous Renters Display:  
  Queries fetch information about previous renters, including students and staff, for the given house.  
  The retrieved information is displayed in separate sections for students and staff.  

  Why it's Interesting:  
  The details page involves complex queries that gather information from multiple tables to present a holistic view of the house.  
  The interplay of retrieving dynamic content, calculating average ratings, and displaying a list of previous renters. 


### References used for HTML 
www.w3school.com  
(no AI tools were used)