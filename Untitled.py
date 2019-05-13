#!/usr/bin/env python
# coding: utf-8

# In[1]:


import socket
import sys
import psutil


# In[2]:


sys.version_info


# In[3]:

hostname = socket.gethostname()
addresses = socket.getaddrinfo(socket.gethostname(), None)

address_info = []
for address in addresses:
    address_info.append((address[0].name, address[4][0]))
address_info

# In[4]:


psutil.cpu_percent()


# In[5]:


psutil.virtual_memory().available


# In[6]:


psutil.sensors_battery().power_plugged


# In[ ]:




