import networkx as nx
from networkx import floyd_warshall_numpy
from numpy import ndarray, save, load
from flaskr.Tools import log, now

class TransactionsGraph:

  def __init__(self,profils=None):
    self.G = nx.DiGraph()
    self.edge_prop=[]
    if profils:
      self.load(profils)


  def filter(self,critere="pagerank",threshold=0):
    _G=self.G.copy()
    for idx in self.G.nodes:
      if not critere in self.G.nodes[idx] or self.G.nodes[idx][critere]<threshold:
        _G.remove_node(idx)
    self.G=_G


  def extract_subgraph(self):
    res=nx.shortest_path(self.G)

  def idx_node(self,profil_id):
    if profil_id:
      for i in range(1,self.G.number_of_nodes()+1):
        if self.G.nodes[i]["id"]==int(profil_id):
          return i
    return None


  def load(self,transactions:[dict],network="elrond-devnet",tokens=dict()):
    ids = []
    visual="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/google/350/person_1f9d1.png"
    for t in transactions:

      self.G.add_node(t["from"],label=t["from"],visual=visual,url="https://"+("devnet-" if "devnet" in network else "")+"explorer.elrond.com/accounts/"+t["from"])
      self.G.add_node(t["to"],label=t["to"],visual=visual,url="https://"+("devnet-" if "devnet" in network else "")+"explorer.elrond.com/accounts/"+t["to"])

      self.G.add_edge(t["from"],t["to"],
                      title=t["method"],
                      id=t["id"],
                      token=tokens[t["token"]] if t["token"] in tokens else t["token"],
                      timestamp=t["ts"],
                      value=t["value"],
                      url="https://"+("devnet-" if "devnet" in network else "")+"explorer.elrond.com/transactions/"+t["id"]
                      )

    return len(self.G.nodes)


  def eval(self,critere="pagerank"):
    if "pagerank" in critere:
      ranks=nx.pagerank(self.G)
      for k in ranks.keys():
        self.G.nodes[k]["pagerank"]=ranks.get(k)

    if "centrality" in critere:
      props=nx.betweenness_centrality(self.G)
      for k in props.keys():
        self.G.nodes[k]["centrality"]=props.get(k)


  def distance(self,filename="social_distance_matrix",delayInHour=2):
    if self.fs.exists(filename) and (now()-self.fs.get_modified_time(filename).timestamp())/(60*60)<delayInHour:
      file=self.fs.open(filename)
      rc=load(file,allow_pickle=True)
    else:
      log("Lancement du calcul de la matrice de distance")
      rc:ndarray=floyd_warshall_numpy(self.G)
      self.fs.delete(filename)
      save(self.fs.open(filename,"wb"),rc,allow_pickle=True)

    return rc



  #http://localhost:8000/api/social_graph/
  def export(self,format="graphml"):
    if format=="gxf":
      filename=TEMP_DIR+"test.gefx"
      nx.write_gexf(self.G, filename,encoding="utf-8")

    if format=="graphml":
      filename=TEMP_DIR+"femis.graphml"
      nx.write_graphml(self.G,filename,encoding="utf-8")


    nodes_with_attr = list()
    for n in self.G.nodes.data():
      n[1]["id"]=n[0]
      nodes_with_attr.append(n[1])

    edges=[]
    for edge in self.G.edges.data():
      edges.append({"source":edge[0],"target":edge[1],"data":edge[2]})

    rc={"graph":{"nodes":nodes_with_attr,"edges":edges},"edge_props":self.edge_prop}
    return rc




