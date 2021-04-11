# Lightricks Web Crawler
author:  Ariel Zerahia
email: arielzarahia@gmail.com

## Naive implementation
Basic implementation, all run on a single process, it saves al the information of the clawled URLs in memory and does not take care of managing a secure access to common resources.

But still it is build to be easily converted into a distributed implementation. This can be achieved by replacing the `URLsManager` class implementation with:
1. database for storing the URL's information
1. queue for managing the crawling tasks
1. some locking mechanism

