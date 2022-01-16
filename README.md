# vQueue
I made this app during the coronavirus pandemic. Due to pandemic-related capacity restrictions, there were often long lineups outside of local stores, which were both unsafe and inconvenient for shoppers. vQueue allowed stores to create virtual queues that shoppers could join using SMS, thereby eliminating the need for physical lines altogether.

Here's a [demo](https://youtu.be/QLto5lJytTs) of the project (unlisted on YouTube).

### Usage
```sh
$ git clone https://github.com/karmdesai/vQueue.git
$ cd vQueue
$ pip3 install -r requirements.txt
$ export FLASK_APP=vQueue.py
$ flask run
```

Please note that you will also have to export/set the environment variables. These include MongoDB credentials (for storing data about a business and its clients), Twilio credentials (for sending and receiving text messages), Mail credentials (for password reset).

### To-Do
- [ ] Improve styling and UI.
- [ ] Add a home page describing what the app does.