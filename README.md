#  Pulling data from Rational Quality Manager (RQM) using REST API in python
## Background:

I was developing tools to generate report based on RQM data and other sources. I was using RQMURLUtility to pull the data. Only problem I was facing was slow response as I had to make hundreds of API calls. Every time we call RQMURLUtility, it will authenticate and then pull the data. I though of optimizing it by authenticating once and reusing the session for multiple calls. After a bit of research I found that login is based on form authentication. The solution that I found is:

- Created a Session 
- Login once 
- Reuse to make many REST API calls

