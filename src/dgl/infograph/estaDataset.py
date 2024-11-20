import os
import pickle

import networkx as nx
import dgl
from dgl.data import DGLDataset
from dgl.data.utils import load_graphs, save_graphs
class EstaDataset(DGLDataset):
  """ Template for customizing graph datasets in DGL.

  Parameters
  ----------
  url : str
      URL to download the raw dataset
  raw_dir : str
      Specifying the directory that will store the
      downloaded data or the directory that
      already stores the input data.
      Default: ~/.dgl/
  save_dir : str
      Directory to save the processed dataset.
      Default: the value of `raw_dir`
  force_reload : bool
      Whether to reload the dataset. Default: False
  verbose : bool
      Whether to print out progress information
  """
  def __init__(self,
               url=None,
               raw_dir=None,
               save_dir=None,
               force_reload=False,
               verbose=False):
    super(EstaDataset, self).__init__(name='esta',
                                    url=url,
                                    raw_dir=raw_dir,
                                    save_dir=save_dir,
                                    force_reload=force_reload,
                                    verbose=verbose)

  def download(self):
    # download raw data to local disk
    pass

  def _load_graphs_from_list_of_dicts(self, filename, create_using=nx.DiGraph):
    # from https://stackoverflow.com/questions/62615933/how-to-store-multiple-networkx-graphs-in-one-file
    with open(filename, 'rb') as f:
      list_of_dicts = pickle.load(f)
    return [create_using(graph) for graph in list_of_dicts]

  def process(self):
    nxgraphs = []
    for file_round in os.listdir(self.raw_dir):
      nxgraphs.extend(self._load_graphs_from_list_of_dicts(os.path.join(self.raw_dir, file_round)))

    node_attributes = None # ["x", "y", "z"]
    edge_attributes = ["dist",]
    # process data to a list of graphs and a list of labels
    # todo remove conersion and do it in create_graphs.py
    self.graphs = [dgl.from_networkx(nx.convert_node_labels_to_integers(graph), node_attrs=node_attributes, edge_attrs=edge_attributes) for graph in nxgraphs]
    self.label = [None] * len(nxgraphs)

  def __getitem__(self, idx):
    """ Get graph and label by index

    Parameters
    ----------
    idx : int
        Item index

    Returns
    -------
    (dgl.DGLGraph, Tensor)
    """
    return self.graphs[idx], self.label[idx]

  def __len__(self):
    """Number of graphs in the dataset"""
    return len(self.graphs)


def save(self):
  """save the graph list and the labels"""
  graph_path = os.path.join(self.save_path, 'dgl_graph.bin')
  save_graphs(str(graph_path), self.graphs, {'labels': self.label})


def has_cache(self):
  graph_path = os.path.join(self.save_path, 'dgl_graph.bin')
  return os.path.exists(graph_path)


def load(self):
  graphs, label_dict = load_graphs(os.path.join(self.save_path, 'dgl_graph.bin'))
  self.graphs = graphs
  self.label = label_dict['labels']


@property
def num_labels(self):
  """Number of labels for each graph, i.e. number of prediction tasks."""
  return 0

def __getitem__(self, idx):
  r""" Get graph and label by index

  Parameters
  ----------
  idx : int
      Item index

  Returns
  -------
  (:class:`dgl.DGLGraph`, Tensor)
  """
  return self.graphs[idx], self.label[idx]

def __len__(self):
  r"""Number of graphs in the dataset.

  Return
  -------
  int
  """
  return len(self.graphs)


if __name__ == "__main__":
  # test loading dataset
  dataset = EstaDataset(raw_dir="/mnt/d/dev/csgo-analysis/graphs/00e7fec9-cee0-430f-80f4-6b50443ceacd")
  print("Number of graphs:", len(dataset))
  g = dataset[0]
  # print("Node features:")
  # print(g.ndata)
  # print("Edge features")
  # print(g.edata)