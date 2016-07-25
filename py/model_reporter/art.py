from . import docx, latex, pdf, txt, xhtml, alogit
import math
from ..util.xhtml import XHTML, XML_Builder, Elem
from ..util.pmath import category, pmath, rename
from ..core import LarchError
import os
import pandas
import numpy
import itertools




class colorize:
	_PURPLE = '\033[95m'
	_CYAN = '\033[96m'
	_DARKCYAN = '\033[36m'  # colorama ok
	_BLUE = '\033[94m'
	_GREEN = '\033[32m'
	_LIGHTGREEN = '\033[92m'
	_BOLDGREEN = '\033[92;1m'
	_YELLOW = '\033[93m'
	_REDBRIGHT = '\033[91m'
	_RED = '\033[31m'
	_BOLD = '\033[1m'
	_UNDERLINE = '\033[4m'
	_END = '\033[0m'
	@classmethod
	def bold(cls, x):
		return cls._BOLD + str(x) + cls._END
	@classmethod
	def red1(cls, x):
		return cls._REDBRIGHT + str(x) + cls._END
	@classmethod
	def red(cls, x):
		return cls._RED + str(x) + cls._END
	@classmethod
	def boldgreen(cls, x):
		return cls._GREEN + cls._BOLD+ str(x) + cls._END
	@classmethod
	def green(cls, x):
		return cls._GREEN +  str(x) + cls._END




class AbstractReportTable():
	def __init__(self, columns=(), col_classes=()):
		self.df = pandas.DataFrame(columns=columns, index=pandas.RangeIndex())
		self.col_classes = col_classes
		self.n_thead_rows = 1
		self.silent_first_col_break = False
		self._col_width = None
		self.title = None
		self.short_title = None
	def add_blank_row(self):
		self.df.loc[len(self.df)] = None
		self._col_width = None
	def encode_cell_value(self, value, attrib=None, tag='td', anchorlabel=None):
		if pandas.isnull(value):
			return None
		if attrib is None:
			attrib = {}
		if isinstance(value, Elem):
			value.tag = tag
			for k,v in attrib.items():
				if k=='class':
					v1 = value.get(k,None)
					if v1 is not None and v not in v1:
						v = "{} {}".format(v,v1)
				value.set(k,v)
			return value
		if anchorlabel is None:
			e = Elem(tag=tag, text=str(value), attrib=attrib)
		else:
			e = Elem(tag=tag, attrib=attrib)
			e.append(Elem(tag='a', attrib={'name':str(anchorlabel)}, tail=str(value)))
		return e
	def encode_head_value(self, value, attrib=None):
		return self.encode_cell_value(value, attrib=attrib, tag='th')
	def addrow_seq_of_strings(self, str_content, attrib={}):
		if len(str_content) > len(self.df.columns):
			raise TypeError("Insufficient columns for new row")
		self.add_blank_row()
		for n,s in enumerate(str_content):
			self.df.iloc[-1,n] = self.encode_cell_value(s)
	def addrow_map_of_strings(self, str_content, attrib={}):
		self.add_blank_row()
		rowix = self.df.index[-1]
		for key,val in str_content.items():
			self.df.loc[rowix, key] = self.encode_cell_value(val)

	def set_lastrow_loc(self, colname, val, attrib=None, anchorlabel=None):
		rowix = self.df.index[-1]
		self.df.loc[rowix, colname] = self.encode_cell_value(val, attrib, anchorlabel=anchorlabel)
		self._col_width = None
	def set_lastrow_iloc(self, colnum, val, attrib=None, anchorlabel=None):
		self.df.iloc[-1, colnum] = self.encode_cell_value(val, attrib, anchorlabel=anchorlabel)
		self._col_width = None
	def set_lastrow_iloc_nondupe(self, colnum, val, attrib=None, anchorlabel=None):
		try:
			val_text = val.text
		except AttributeError:
			val_text = str(val)
		prev = -1
		prev_text = None
		try:
			while prev_text is None:
				prev -= 1
				prev_text = self.get_text_iloc(prev,colnum, missing=None)
			if prev_text!=val_text:
				raise NameError
		except (NameError, IndexError):
			self.df.iloc[-1, colnum] = self.encode_cell_value(val, attrib, anchorlabel=anchorlabel)
			self._col_width = None

	def __repr__(self):
		if self.title:
			s = " {}\n".format(colorize.boldgreen(self.title))
		else:
			s = ""
		s += self.unicodebox()
		return s

	def _dividing_line(self, leftend="+", rightend="+", splitpoint="+", linechar="─"):
		lines = [linechar*w for w in self.min_col_widths_()]
		return leftend+splitpoint.join(lines)+rightend

	def __str__(self):
		if self.title:
			s = " {}\n".format(self.title)
		else:
			s = ""
		s += self.unicodebox()
		return s

	def _text_output(self, topleft   ='┌', topsplit   ='┬', topright   ='┐',
	                       middleleft='├', middlesplit='┼', middleright='┤',
	                       bottomleft='└', bottomsplit='┴', bottomright='┘',
						   leftvert  ='│', othervert  ='│',
						   horizbar='─',
						   catleft='╞', catright='╡', cathorizbar='═',
						   ):
		s = self._dividing_line(leftend=topleft, rightend=topright, splitpoint=topsplit, linechar=horizbar)+"\n"
		w = self.min_col_widths()
		for r,rvalue in enumerate(self.df.index):
			if (~pandas.isnull(self.df.iloc[r,1:])).sum()==0:
				catflag = True
			else:
				catflag = False
			if r==self.n_thead_rows and self.n_thead_rows>0:
				s += self._dividing_line(leftend=middleleft, rightend=middleright, splitpoint=middlesplit, linechar=horizbar)+"\n"
			startline = True
			s += leftvert
			for c,cvalue in enumerate(self.df.columns):
				cellspan = self.cellspan_iloc(r,c)
				if cellspan != (0,0):
					cw = numpy.sum(w[c:c+cellspan[1]])+cellspan[1]-1
					if catflag:
						s = s[:-len(leftvert)]+ catleft+" {1:{2}<{0}s}".format(cw-1,self.get_text_iloc(r,c).replace('\t'," ")+" ",cathorizbar)+catright
					else:
						s += "{1:{0}s}".format(cw,self.get_text_iloc(r,c).replace('\t'," "))+othervert
					startline = False
				elif cellspan == (0,0) and startline:
					cw = w[c]
					s += "{1:{0}s}".format(cw,"")+othervert
				else:
					startline = False
			s += "\n"
		s += self._dividing_line(leftend=bottomleft, rightend=bottomright, splitpoint=bottomsplit, linechar=horizbar)
		return s



	def unicodebox(self):
#		s = self._dividing_line(leftend='┌', rightend='┐', splitpoint='┬')+"\n"
#		w = self.min_col_widths()
#		for r,rvalue in enumerate(self.df.index):
#			if (~pandas.isnull(self.df.iloc[r,1:])).sum()==0:
#				catflag = True
#			else:
#				catflag = False
#			if r==self.n_thead_rows and self.n_thead_rows>0:
#				s += self._dividing_line(leftend='├', rightend='┤', splitpoint='┼')+"\n"
#			startline = True
#			s += "│"
#			for c,cvalue in enumerate(self.df.columns):
#				cellspan = self.cellspan_iloc(r,c)
#				if cellspan != (0,0):
#					cw = numpy.sum(w[c:c+cellspan[1]])+cellspan[1]-1
#					if catflag:
#						s = s[:-1]+ "╞ {1:═<{0}s}╡".format(cw-1,self.get_text_iloc(r,c)+" ")
#					else:
#						s += "{1:{0}s}│".format(cw,self.get_text_iloc(r,c))
#					startline = False
#				elif cellspan == (0,0) and startline:
#					cw = w[c]
#					s += "{1:{0}s}│".format(cw,"")
#				else:
#					startline = False
#			s += "\n"
#		s += self._dividing_line(leftend='└', rightend='┘', splitpoint='┴')
#		return s
		return self._text_output()

	def tabdelim(self):
#		s = self._dividing_line(leftend='', rightend='', splitpoint='\t')+"\n"
#		w = self.min_col_widths()
#		for r,rvalue in enumerate(self.df.index):
#			if (~pandas.isnull(self.df.iloc[r,:])).sum()==1:
#				catflag = True
#			else:
#				catflag = False
#			if r==self.n_thead_rows:
#				s += self._dividing_line(leftend='', rightend='', splitpoint='\t')+"\n"
#			startline = True
#			for c,cvalue in enumerate(self.df.columns):
#				cellspan = self.cellspan_iloc(r,c)
#				if cellspan != (0,0):
#					cw = numpy.sum(w[c:c+cellspan[1]])+cellspan[1]-1
#					if catflag:
#						s = s[:-1]+ " {1: <{0}s}".format(cw-1,self.get_text_iloc(r,c)+" ")
#					else:
#						s += "{1:{0}s}\t".format(cw,self.get_text_iloc(r,c))
#					startline = False
#				elif cellspan == (0,0) and startline:
#					cw = w[c]
#					s += "{1:{0}s}\t".format(cw,"")
#				else:
#					startline = False
#			s += "\n"
#		s += self._dividing_line(leftend='', rightend='', splitpoint='\t')
#		return s
		return self._text_output(  topleft   ='', topsplit   ='\t', topright   ='',
								   middleleft='', middlesplit='\t', middleright='',
								   bottomleft='', bottomsplit='\t', bottomright='',
								   leftvert  ='', othervert  ='\t', horizbar='-',
								   catleft='', catright='', cathorizbar=' ')

	def ascii(self):
		return self._text_output(  topleft   ='+', topsplit   ='+', topright   ='+',
								   middleleft='+', middlesplit='+', middleright='+',
								   bottomleft='+', bottomsplit='+', bottomright='+',
								   leftvert  =' ', othervert  =' ', horizbar='-',
								   catleft='=', catright='=', cathorizbar='=')

	def xml(self, table_attrib=None, headlevel=2):
		table = Elem(tag='table', attrib=table_attrib or {})
		thead = table.put('thead')
		tbody = table.put('tbody')
		tfoot = table.put('tfoot')
		r = 0
		while r<len(self.df.index):
			if r<self.n_thead_rows:
				tr = thead.put('tr')
				celltag = 'th'
			else:
				tr = tbody.put('tr')
				celltag = 'td'
			span = 1
			for c in range(len(self.df.columns)):
				attrib = {}
				try:
					attrib['class'] = self.col_classes[c]
				except:
					pass
				td = self.encode_cell_value(  self.df.iloc[r,c] , attrib=attrib, tag=celltag )
				if td is None:
					try:
						tr[-1].get('colspan','1')
					except IndexError:
						# check if first cell in row, and cell above is same value
						if c==0:
							rc_text, rx, cx = self.get_implied_text_iloc(r,c)
							if rx<0:
								try:
									tbody[rx-1][0].set('rowspan',str(1-rx))
									tbody[rx-1][0].set('style','vertical-align:top;')
								except IndexError:
									tr << self.encode_cell_value(  "" , attrib=attrib, tag=celltag )
							else:
								tr << self.encode_cell_value(  "" , attrib=attrib, tag=celltag )
						else:
							tr << self.encode_cell_value(  "" , attrib=attrib, tag=celltag )
					else:
						span += 1
						tr[-1].set('colspan',str(span))
				else:
					tr << td
					span = 1
			r += 1
		if headlevel is not None and self.title is not None:
			try:
				headlevel = int(headlevel)
			except:
				pass
			else:
				div = XML_Builder("div")
				div.h2(self.title, anchor=self.short_title or self.title)
				div << table
				return div.close()
		return table

	def cellspan_iloc(self,r,c):
		try:
			if pandas.isnull(self.df.iloc[r,c]):
				return (0,0)
		except:
			print("r:",r,type(r))
			print("c:",c,type(c))
			raise
		x,y = 1,1
		while r+y < len(self.df.index) and numpy.all(pandas.isnull(self.df.iloc[r+y,:c+1])):
			y += 1
		while c+x < len(self.df.columns) and pandas.isnull(self.df.iloc[r,c+x]):
			x += 1
		return (y,x)

	def get_text_iloc(self,r,c,missing=""):
		if pandas.isnull(self.df.iloc[r,c]):
			return missing
		txt = (self.df.iloc[r,c].text or "")
		for subelement in self.df.iloc[r,c]:
			txt += (subelement.text or "") + (subelement.tail or "")
		return txt

	def get_implied_text_iloc(self,r,c,missing=""):
		"""Get the implied text value of the field after merges, and the source cell.
		
		Parameters
		----------
		r : int
			The row of the cell to get
		c : int
			The columns of the cell to get
		missing : str
			Text to return if there is no implied text value
		
		Returns
		-------
		str
			The implied text value
		int
			The offset to the row of the cell generating this value
		int
			The offset to the column of the cell generating this value
		
		"""
		cx = c
		rx = r
		if c==0 and pandas.isnull(self.df.iloc[r,c]):
			# first column, null value so look up
			while rx>0 and pandas.isnull(self.df.iloc[rx,cx]):
				rx -=1
			if pandas.isnull(self.df.iloc[rx,cx]):
				return missing, 0, 0
			else:
				return self.df.iloc[rx,cx].text, rx-r, cx-c
		while cx>0 and pandas.isnull(self.df.iloc[r,cx]):
			cx -= 1
		if pandas.isnull(self.df.iloc[r,cx]):
			return missing, 0, 0
		return self.df.iloc[rx,cx].text, rx-r, cx-c

	def min_col_widths(self):
		if self._col_width is not None:
			return self._col_width
		w = numpy.zeros(len(self.df.columns), dtype=int)
		for r,c in itertools.product(range(len(self.df.index)),range(len(self.df.columns))):
			if self.cellspan_iloc(r,c)[1]==1:
				w[c] = max(w[c], len(self.get_text_iloc(r,c)))
		for span in range(2,len(self.df.columns)):
			for r,c in itertools.product(range(len(self.df.index)),range(len(self.df.columns))):
				if self.cellspan_iloc(r,c)[1]==span:
					shortage = len(self.get_text_iloc(r,c))  -   (numpy.sum(w[c:c+span])+span-1)
					if shortage>0:
						w[c] += shortage
		self._col_width = w
		return w

	def min_col_widths_(self):
		w = self.min_col_widths()
		if self.silent_first_col_break:
			ww = w[1:].copy()
			ww[0] += 1+w[0]
			return ww
		else:
			return w







class ArtModelReporter():

	def art_params(self, groups=None, display_inital=False, display_id=False, **format):
		"""
		Generate a div element containing the model parameters in a table.
		
		Parameters
		----------
		groups : None or list
			An ordered list of parameters names and/or categories. If given,
			this list will be used to order the resulting table.
		display_inital : bool
			Should the initial values of the parameters (the starting point 
			for estimation) be included in the report. Defaults to False.
		display_id : bool
			Should the actual parameter names be shown in an id column.
			Defaults to False.  This can be useful if the groups include 
			renaming.
		
		Returns
		-------
		AbstractReportTable
			An ART containing the model parameters.
		
		"""
		# keys fix
		existing_format_keys = list(format.keys())
		for key in existing_format_keys:
			if key.upper()!=key: format[key.upper()] = format[key]
		if 'PARAM' not in format: format['PARAM'] = '< 10.4g'
		if 'TSTAT' not in format: format['TSTAT'] = ' 0.2f'
		# build table

		columns = ["Parameter", None, "Estimated Value", "Std Error", "t-Stat", "Null Value"]
		col_classes = ['param_label','param_label', 'estimated_value', 'std_err', 'tstat', 'null_value']
		if display_inital:
			columns.insert(1,"Initial Value")
			col_classes.insert(1,'initial_value')
		if display_id:
			columns.append('id')
			col_classes.append('id')

		x = AbstractReportTable(columns=columns, col_classes=col_classes)
		x.silent_first_col_break = True
		x.title = "Model Parameter Estimates"
		x.short_title="Parameter Estimates"

		if groups is None and hasattr(self, 'parameter_groups'):
			groups = self.parameter_groups
		if groups is None:
			groups = ()
			
		## USING GROUPS
		listed_parameters = set([p for p in groups if not isinstance(p,category)])
		for p in groups:
			if isinstance(p,category):
				listed_parameters.update( p.complete_members() )
		unlisted_parameters_set = (set(self.parameter_names()) | set(self.alias_names())) - listed_parameters
		unlisted_parameters = []
		for pname in self.parameter_names():
			if pname in unlisted_parameters_set:
				unlisted_parameters.append(pname)
		for pname in self.alias_names():
			if pname in unlisted_parameters_set:
				unlisted_parameters.append(pname)
		n_cols_params = 6 if display_inital else 5
		if display_id:
			n_cols_params += 1
		
		def write_param_row(p, *, force=False):
			if p is None: return
			if force or (p in self) or (p in self.alias_names()):
				if isinstance(p,category):
					x.add_blank_row()
					x.set_lastrow_iloc(0, p.name, {'class':"parameter_category"})
					for subp in p.members:
						write_param_row(subp)
				else:
					if isinstance(p,(rename, )):
						p_name = p.name
					else:
						p_name = p
					x.add_blank_row()
					if "#" in p_name:
						p_name1, p_name2 = p_name.split("#",1)
						x.set_lastrow_iloc_nondupe(0, p_name1, )
						x.set_lastrow_iloc(1, p_name2, anchorlabel="param"+p_name2.replace("#","_hash_"))
					elif ":" in p_name:
						p_name1, p_name2 = p_name.split(":",1)
						x.set_lastrow_iloc_nondupe(0, p_name1, )
						x.set_lastrow_iloc(1, p_name2, anchorlabel="param"+p_name2.replace("#","_hash_"))
					else:
						x.set_lastrow_loc('Parameter', p_name, anchorlabel="param"+p_name.replace("#","_hash_"))
					self.art_single_parameter_resultpart(x,p, with_inital=display_inital, **format)
					if display_id:
						if isinstance(p,(rename, )):
							p_id = p.find_in(self)
						else:
							p_id = p
						x.set_lastrow_loc('id', p_id)
		
		x.addrow_seq_of_strings(columns)
		for p in groups:
			write_param_row(p)
		if len(groups)>0 and len(unlisted_parameters)>0:
			write_param_row(category("Other Parameters"),force=True)
		if len(unlisted_parameters)>0:
			for p in unlisted_parameters:
				write_param_row(p)
		return x



	def art_single_parameter_resultpart(self, ART, p, *, with_inital=False,
										  with_stderr=True, with_tstat=True,
										  with_nullvalue=True, tstat_parens=False, **format):
		if p is None: return
		with_stderr = bool(with_stderr)
		with_tstat = bool(with_tstat)
		with_nullvalue = bool(with_nullvalue)
		#x = XML_Builder("div", {'class':"parameter_estimate"})
		x= ART
		if isinstance(p,(rename,str)):
			try:
				model_p = self[p]
			except KeyError:
				use_shadow_p = True
			else:
				use_shadow_p = False
			if use_shadow_p:
				# Parameter not found, try shadow_parameter
				try:
					str_p = str(p.find_in(self))
				except AttributeError:
					str_p = p
				shadow_p = self.shadow_parameter[str_p]
				if with_inital:
					x.set_lastrow_loc('Initial Value', "")
				shadow_p_value = shadow_p.value
				x.set_lastrow_loc('Estimated Value', "{:{PARAM}}".format(shadow_p.value, **format))
				#x.td("{:{PARAM}}".format(shadow_p.value, **format), {'class':'estimated_value'})
				x.set_lastrow_loc('Std Error', "{}".format(shadow_p.t_stat))
				#x.td("{}".format(shadow_p.t_stat), {'colspan':str(with_stderr+with_tstat+with_nullvalue), 'class':'tstat'})
			else:
				# Parameter found, use model_p
				if with_inital:
					x.set_lastrow_loc('Initial Value', "{:{PARAM}}".format(model_p.initial_value, **format))
					#x.td("{:{PARAM}}".format(model_p.initial_value, **format), {'class':'initial_value'})
				x.set_lastrow_loc('Estimated Value', "{:{PARAM}}".format(model_p.value, **format))
				#x.td("{:{PARAM}}".format(model_p.value, **format), {'class':'estimated_value'})
				if model_p.holdfast:
					x.set_lastrow_loc('Std Error', "fixed value")
					#x.td("fixed value", {'colspan':str(with_stderr+with_tstat), 'class':'notation'})
					x.set_lastrow_loc('Null Value', "{:{PARAM}}".format(model_p.null_value, **format))
					#x.td("{:{PARAM}}".format(model_p.null_value, **format), {'class':'null_value'})
				else:
					tstat_p = model_p.t_stat
					if isinstance(tstat_p,str):
						x.set_lastrow_loc('Std Error', "{}".format(tstat_p))
						#x.td("{}".format(tstat_p), {'colspan':str(with_stderr+with_tstat+with_nullvalue), 'class':'tstat'})
					elif tstat_p is None:
						x.set_lastrow_loc('Std Error', "{:{PARAM}}".format(model_p.std_err, **format))
						#x.td("{:{PARAM}}".format(model_p.std_err, **format), {'class':'std_err'})
						x.set_lastrow_loc('t-Stat', "None")
						#x.td("None", {'class':'tstat'})
						x.set_lastrow_loc('Null Value', "{:{PARAM}}".format(model_p.null_value, **format))
						#x.td("{:{PARAM}}".format(model_p.null_value, **format), {'class':'null_value'})
					else:
						x.set_lastrow_loc('Std Error', "{:{PARAM}}".format(model_p.std_err, **format))
						#x.td("{:{PARAM}}".format(model_p.std_err, **format), {'class':'std_err'})
						x.set_lastrow_loc('t-Stat', "{:{TSTAT}}".format(tstat_p, **format))
						#x.td("{:{TSTAT}}".format(tstat_p, **format), {'class':'tstat'})
						x.set_lastrow_loc('Null Value', "{:{PARAM}}".format(model_p.null_value, **format))
						#x.td("{:{PARAM}}".format(model_p.null_value, **format), {'class':'null_value'})
		#return x.close()



	def art_latest(self,**format):
		from ..utilities import format_seconds
		existing_format_keys = list(format.keys())
		for key in existing_format_keys:
			if key.upper()!=key: format[key.upper()] = format[key]
		if 'LL' not in format: format['LL'] = '0.2f'
		if 'RHOSQ' not in format: format['RHOSQ'] = '0.3f'
	
		es = self._get_estimation_statistics()

		x = AbstractReportTable(columns=["attr", "subattr", "value", ])
		x.silent_first_col_break = True
		x.n_thead_rows = 0
		
		x.title = "Latest Estimation Run Statistics"
		x.short_title = "Latest Estimation Run"

		last = self.maximize_loglike_results
		try:
			last_stat = last.stats
		except AttributeError:
			pass
		else:
			x.add_blank_row()
			x.set_lastrow_iloc(0, "Estimation Date")
			x.set_lastrow_iloc(2, last_stat.timestamp)

			x.add_blank_row()
			x.set_lastrow_iloc(0, "Results")
			x.set_lastrow_iloc(2, last_stat.results)

			if len(last.intermediate) > 1:
				x.add_blank_row()
				x.set_lastrow_iloc(0, "Messages")
				x.set_lastrow_iloc(1, "Final")
				x.set_lastrow_iloc(2, str(last.message))
				for intermed in last.intermediate:
					x.add_blank_row()
					x.set_lastrow_iloc_nondupe(0, "Messages")
					x.set_lastrow_iloc(1, intermed.method)
					x.set_lastrow_iloc(2, intermed.message)
			else:
				x.add_blank_row()
				x.set_lastrow_iloc(0, "Message")
				x.set_lastrow_iloc(2, str(last.message))
				x.add_blank_row()
				x.set_lastrow_iloc(0, "Optimization Method")
				x.set_lastrow_iloc(2, last.intermediate[0].method)
			

			if len(last.niter) > 1:
				x.add_blank_row()
				x.set_lastrow_iloc(0, "Number of Iterations")
				x.set_lastrow_iloc(1, "Total")
				x.set_lastrow_iloc(2, last_stat.iteration)
				for iter in last.niter:
					x.add_blank_row()
					x.set_lastrow_iloc_nondupe(0, "Number of Iterations")
					x.set_lastrow_iloc(1, iter[0])
					x.set_lastrow_iloc(2, iter[1])
			else:
				x.add_blank_row()
				x.set_lastrow_iloc(0, "Number of Iterations")
				x.set_lastrow_iloc(2, last_stat.iteration)
			
			seconds = last_stat.dictionary()['total_duration_seconds']
			tformat = "{}\t{}".format(*format_seconds(seconds))
			x.add_blank_row()
			x.set_lastrow_iloc_nondupe(0, "Running Time")
			x.set_lastrow_iloc(1, "Total")
			x.set_lastrow_iloc(2, "{0}".format(tformat,**format))
			for label, dur in zip(last_stat.process_label,last_stat.dictionary()['process_durations']):
				x.add_blank_row()
				x.set_lastrow_iloc_nondupe(0, "Running Time")
				x.set_lastrow_iloc(1, label)
				x.set_lastrow_iloc(2, "{0}".format(dur,**format))
				
			i = last_stat.notes()
			if i is not '':
				if isinstance(i,list):
					if ii in i:
						x.add_blank_row()
						x.set_lastrow_iloc_nondupe(0, "Notes")
						x.set_lastrow_iloc(2, str(ii))
				else:
					x.add_blank_row()
					x.set_lastrow_iloc_nondupe(0, "Notes")
					x.set_lastrow_iloc(2, str(i))

			i = last_stat.processor
#			try:
#				from ..util.sysinfo import get_processor_name
#				i2 = get_processor_name()
#				if isinstance(i2,bytes):
#					i2 = i2.decode('utf8')
#			except:
#				i2 = None
#			if i is not '':
#				x.add_blank_row()
#				x.set_lastrow_iloc(0, "Processor")
#				x.set_lastrow_iloc(2, str(i))
#				if i2 is not None:
#					x.add_blank_row()
#					x.set_lastrow_iloc_nondupe(0, "Processor")
#					x.set_lastrow_iloc(1, "Detail")
#					x.set_lastrow_iloc(2, str(i2))
			x.add_blank_row()
			x.set_lastrow_iloc(0, "Processor")
			x.set_lastrow_iloc(2, i)

			x.add_blank_row()
			x.set_lastrow_iloc(0, "Number of CPU Cores")
			x.set_lastrow_iloc(2, last_stat.number_cpu_cores)

			x.add_blank_row()
			x.set_lastrow_iloc(0, "Number of Threads Used")
			x.set_lastrow_iloc(2, last_stat.number_threads)

			# installed memory
#			try:
#				import psutil
#			except ImportError:
#				pass
#			else:
#				mem = psutil.virtual_memory().total
#				if mem >= 2.0*2**30:
#					mem_size = str(mem/2**30) + " GiB"
#				else:
#					mem_size = str(mem/2**20) + " MiB"
#				x.add_blank_row()
#				x.set_lastrow_iloc(0, "Installed Memory")
#				x.set_lastrow_iloc(2, "{0}".format(mem_size,**format))
			try:
				mem_size = last.installed_memory
			except AttributeError:
				pass
			else:
				x.add_blank_row()
				x.set_lastrow_iloc(0, "Installed Memory")
				x.set_lastrow_iloc(2, "{0}".format(mem_size,**format))

			# peak memory usage
			try:
				peak = last.peak_memory_usage
			except AttributeError:
				pass
			else:
				x.add_blank_row()
				x.set_lastrow_iloc(0, "Peak Memory Usage")
				x.set_lastrow_iloc(2, "{0}".format(peak,**format))
		return x
