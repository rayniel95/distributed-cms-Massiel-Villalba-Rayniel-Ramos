# About

The Distributed CMS (Content Management System) was my final project in my Distributed Systems course. The
idea was implement a crash fault tolerant system, this is solved using a [Chord][1] distributed hash table. I used the Chord original paper and modified some algorithms, for example, one adventage of my modified algorithms is that we only need one node for create a chord ring, of course, a problem with this is the high traffic in the network. I try to solve the network partition problem for two partitions saving the new neighbors nodes in a special list and asking if the actual node is not in the ring of that neighbor, a very simple algorithm. Because the system is crash fault tolerant you can add new nodes, add data to the system, deleting node, but the data will be remain in the system (if it have at least one node).

## More

See in this repository:

- `cms-compartido.pdf`
- `chord.pdf`
- `1502.06461.pdf`

# Requirements

## Docker compose network

docker

docker-compose

# How to execute

## Docker compose execution

Execute `sudo docker-compose up`

# How to use

This is a cft system, so, to test it you will need to create faults. This faults can be created removing chord nodes (containers) and wait some time to system stabilisation (1 - 3 minutes). If the data introduced still remain the system work ok.

## How to do a simple test

Ansible playbook will create 5 chords nodes accessible through localhost ports:
5000, 5001, ..., 5004. The web app running over chord try to emulate a cms.

1. Go to `localhost:5000`, you will see (text is in spanish, of course):

![welcome page](/images/welcome.png)

2. Go to `Creador de Widgets`. A widget is a piece of html code and variables. The code use `Jinja` template engine for rendering.

![creador de widgets](/images/creador-de-widgets.png)

3. Introduce widget name in first text box (without spaces), introduce variable names in second textbox, introduce your jinja html code in third textbox. Example:

![ejemplo de widget](/images/widget-example.png)

4. Save it and create other.

![ejemplo de widget 2](/images/widget-example2.png)

5. You can see all widgets in the network in `Lista de widgets`, it can take some time (1 minute, the node need to ask to all others nodes for widgets), take a look:

![lista de widgets](/images/widgets-list.png)

6. Create one page, go to `Disenador de paginas`, you will see many sections. Add the name (without spaces). Instantiate widgets with parameters in the sections selected. Save it.

![lista de widgets](/images/creating-ray-page.png)

7. Go to `Lista de paginas`:

![lista de paginas](/images/pages-list.png)

8. Select the page:

![pagina](/images/ray-page.png)

---

Start removing containers. Select a random container, remove it, wait one minute, select other container, remove it, wait one minute, select other container, remove it, wait one minute, go to `Lista de paginas`. The page will remain available!!!!! This is because system nodes can crash but data will remain (data is replicated). It is a fault tolerant system!!!!!!!!!!!!

[1]: https://en.wikipedia.org/wiki/Chord_(peer-to-peer)#:~:text=In%20computing%2C%20Chord%20is%20a,to%2Dpeer%20distributed%20hash%20table.&text=Chord%20specifies%20how%20keys%20are,node%20responsible%20for%20that%20key.