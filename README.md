# What is this?
This is a __Python__ application that uses __ttkboostrap__ to create the GUI. With this app, users can enter an image of a receipt, the total amount spent, and the date of that purchase.

Once users have finished entering their expense information, they have the option to continue adding as many more expenses that they would like to track! 

__MongoDB__ is used to store user expenses, sort expenses by price ascending, count the total number of expenses saved, display the largest purchase made, and find the sum of all expenses. 

# The Set Up
1) Ensure that you pip installed the following:
   * ttkboostrap
   * pymongo
   * os
   * typing
   * PIL
2) Have MongoDB Compass [installed](https://www.youtube.com/watch?v=gB6WLkSrtJk), as it is used to store your expenses. Launch MongoDB Compass and connect to local host. 
3) Adjust the theme of the app, button colors, and fonts by changing values in `settings.py`
4) Either run the python file through an IDE of your choice OR run it via CMD prompt with `python bought.py`

# Example Use Case
<img src ="https://github.com/bryan-avila/bought/blob/main/use_case_example.png" width="800" height="600">


# Credits
Thanks to Clear Code for guiding the process of allowing users to upload images and displaying that image on a ttk Canvas. Check it out [here](https://youtu.be/mop6g-c5HEY?si=NNGBttziY8uU8Yeq&t=56780)! 

The receipt image found in the use case example can be found [here](https://pixabay.com/vectors/invoice-receipt-to-buy-shopping-1708867/). 

**NOTE:** This app was created for the sole purpose of gaining more experience with ttkboostrap and Python, as well as to have fun coding. This is not an officially deployed app.  
