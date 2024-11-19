from dgl.data import DGLDataset

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
    super(EstaDataset, self).__init__(name='dataset_name',
                                    url=url,
                                    raw_dir=raw_dir,
                                    save_dir=save_dir,
                                    force_reload=force_reload,
                                    verbose=verbose)

  def download(self):
    # download raw data to local disk
    pass


  def process(self):
    mat_path = self.raw_path + '.mat'
    # process data to a list of graphs and a list of labels
    self.graphs, self.label = self._load_graph(mat_path)

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
    # save processed data to directory `self.save_path`
    pass

  def load(self):
    # load processed data from directory `self.save_path`
    pass

  def has_cache(self):
    # check whether there are processed data in `self.save_path`
    pass