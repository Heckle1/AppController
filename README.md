# AppController

AppController is a cloud auto-sclaing framework.

## Branches

 * release : stable branch ready for production
 * develop : developpment branch

## Directory tree

  * core : main directory, contains all intelligence
  * libs: all libraries required by core program
  * libs/mon : all monitoring libs required by core to get in touch with monitoring system
  * libs/cloud : all cloud libs required by core to get connected to a cloud API

## Core

Core is the main part of this program. Core can perform a bunch of actions :

 * deploy virtual instances
 * destroy virtual instances

 To create or duplicate more exactly a virtual instance core will have to perform :

  * get master instance id - a healthy instance
  * get informations about master instance
    * block storage attached ( sring )
    * tags ( dict )
    * instance type - vCore and RAM ( string )
    * keypair ( string )
    * security groups ( dict )
    * region ( srting )
    * zone ( string )
  * build a master from a running instance
  * use this master to launch new instances
  * destroy master

Requirements to launch virtual instances :

  * master id ( string )
  * region ( string )
  * zone ( string )
  * keypair ( string )
  * security groups ( dict )

Requirements to destroy virtual instances :

  * virtual instance id ( string )

## Events

Several events can trigger AppController core :

  * url not responding within timeout
  * cpu usage over treshold
  * memory usage over treshold

How to get back to the initial values ?

  * url is responding within timeout
  AND
  * cpu usage on all hosts are under treshold
  AND
  * memory usage on all hosts are under treshold

then decrease the number of virtual instance.
