
import numpy, pandas
from .parameter_collection import ParameterCollection
from .data_collection import DataCollection
from .workspace_collection import WorkspaceCollection

from .nesting.nl_utility import exp_util_of_nests, util_of_nests, exp_inplace_2
from .nesting.nl_prob import conditional_logprob_from_tree_util, elemental_logprob_from_conditional_logprob, total_prob_from_log_conditional_prob

from functools import lru_cache

class Model(ParameterCollection):

	def __init__(self, *,
				 parameters = (),
				 alts = (),
				 datasource = None,
				 **kwarg):

		self._datasource = datasource
		if datasource is not None:
			if isinstance(alts, (numpy.ndarray, pandas.Series, pandas.DataFrame, list, tuple, set)) and len(alts)>0:
				pass # use the override alts
			else:
				alts = datasource.alternative_codes()

		super().__init__(names=parameters, altindex=alts, **kwarg)

		self.data = None
		self.work = None


	@property
	def graph(self):
		return self._graph

	@graph.setter
	def graph(self, value):
		self._set_graph(value)
		if self.work is not None:
			self.work = WorkspaceCollection(data_coll=self.data, parameter_coll=self, graph=self._graph)


	def load_data(self):
		self.data = DataCollection(
			caseindex=None, altindex=self._altindex, source=self._datasource,
			utility_ca_index=self.utility_ca_vars,
			utility_co_index=self.utility_co_vars,
			quantity_ca_index=self.quantity_ca_vars,
		)
		self.data.load_data(source=self._datasource)
		self.work = WorkspaceCollection(data_coll=self.data, parameter_coll=self, graph=self._graph)

	def calculate_utility(self):
		self.data._calculate_utility_elemental(self, self.work.util_elementals)
		util_of_nests(self.work.util_elementals, self.work.util_nests, self._graph, self)

	def calculate_utility_values(self, parameter_values=None):
		self.unmangle()
		if parameter_values is not None:
			self.set_values(parameter_values)
		self.calculate_utility()
		return self.work.util_elementals, self.work.util_nests

	def calculate_log_probability(self):
		conditional_logprob_from_tree_util(
			self.work.util_elementals,
			self.work.util_nests,
			self._graph,
			self,
			self.work.log_conditional_prob_dict
		)
		elemental_logprob_from_conditional_logprob(
			self.work.log_conditional_prob_dict,
			self._graph,
			self.work.log_prob
		)
		total_prob_from_log_conditional_prob(
			self.work.log_conditional_probability,
			self._graph,
			self.work.total_probability,  # shape = (cases, nodes)
		)


	def calculate_probability_values(self, parameter_values=None):
		self.unmangle()
		if parameter_values is not None:
			self.set_values(parameter_values)
		self.calculate_utility()
		self.calculate_log_probability()
		return self.work.total_probability

	def loglike(self, parameter_values=None):
		self.unmangle()
		if parameter_values is not None:
			self.set_values(parameter_values)
		self.calculate_utility()
		self.calculate_log_probability()
		LL = self.data._calculate_log_like(self.work.log_prob)
		return LL

	def loglike_casewise(self, parameter_values=None):
		self.unmangle()
		if parameter_values is not None:
			self.set_values(parameter_values)
		self.calculate_utility()
		self.calculate_log_probability()
		LL = self.data._calculate_log_like_casewise(self.work.log_prob)
		return LL

	def d_loglike(self, parameter_values=None):
		return self._d_loglike_triple(parameter_values=parameter_values)[1]

	def _d_loglike_triple(self, parameter_values=None):
		if parameter_values is not None:
			self.set_values(parameter_values)
		return self.__d_loglike_triple_cache(self.frame.loc[:,'value'].values.tobytes())

	@lru_cache(maxsize=32)
	def __d_loglike_triple_cache(self, parameter_values):
		if not numpy.all(numpy.fromstring(parameter_values) == self.frame.loc[:,'value']):
			print(numpy.fromstring(parameter_values))
			print(self.frame.loc[:,'value'])
			print(numpy.fromstring(parameter_values)-self.frame.loc[:,'value'])
			raise TypeError("must call cached version with current values")
		from .nesting.nl_deriv import _d_loglike
		self.unmangle()
		ll = self.loglike()
		dll, bhhh = _d_loglike(self)
		return ll, dll, bhhh

	def d_loglike_casewise(self, parameter_values=None):
		from .nesting.nl_deriv import _d_loglike_casewise
		return _d_loglike_casewise(self)