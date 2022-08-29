from copy import deepcopy
from collections import defaultdict
from dataclasses import dataclass, field
from pickle import TRUE
import re
import os
from typing import Dict, FrozenSet, Set, List, Tuple
import pandas as pd
import glob
from os.path import join
import os.path as osp
from pathlib import Path
import difflib
from pprint import pprint
import yaml
import random
from tqdm import tqdm
import json
from string_grouper import group_similar_strings
from src.boba.bobarun import BobaRun
from src.boba.lang import Lang
from src.boba.wrangler import DIR_LOG, DIR_SCRIPT

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def frozen_set_to_str(fr_set_tup, orig_decision_dict):
	orig_dict = {}
	for tup in fr_set_tup:
		key, val = tup
		if val == orig_decision_dict[key]:
			continue
		orig_dict[tup[0]] = list(tup[1])
	
	if not orig_dict:
		return 'All Universes'
	return yaml.dump(orig_dict)

def decisions_set_unique(fr_set_tup, orig_decision_dict):
	orig_dict = {}
	for tup in fr_set_tup:
		key, val = tup
		if val == orig_decision_dict[key]:
			continue
		orig_dict[tup[0]] = list(tup[1])
	if not orig_dict:
		return {"All Universes": ["All Options"]}
	return orig_dict

def get_decs(summary_df) -> Dict[str, list]:
	return {c : summary_df[c].unique()
			for c in summary_df.columns[1:]}
	
def set_universe_as_index(summary_df):
	summary_df['universe_num'] = summary_df['Filename'].apply(lambda x: int(x.split('_')[-1].split('.')[0]))
	return summary_df.set_index('universe_num')

@dataclass
class ErrorAggregateInfo:
	unum_shared_lines: Dict[int, Dict[str, Set[int]]] = {}
	decisions_to_lines: Dict[Tuple[Tuple[str, FrozenSet[str]]], List[str]] = {}
	common_lines: Dict[FrozenSet[int], List[str]] = {}
	lines_to_decisions: Dict[str, Tuple[Tuple[str, FrozenSet[str]]]] = {}
	_unum_shared_lines: dict  = field(init=False, repr=False)
	_decisions_to_lines: dict = field(init=False, repr=False)
	_common_lines: dict = field(init=False, repr=False)
	_lines_to_decisions: dict = field(init=False, repr=False)
  
	@property
	def unum_shared_lines(self) -> Dict[int, Dict[str, Set[int]]]:
		"""
		Mapping from unum to a Dict mapping its associated code lines to a set of other universes that 
		share that code.
		Has length number of universes
		"""
		return self._unum_shared_lines
	
	@property
	def decisions_to_lines(self) -> Dict[Tuple[Tuple[str, FrozenSet[str]]], List[str]]:
		"""
		Mapping from a set of decision and options to the code lines which these decisions and options share:
		
		Example key:
			(   
				('M', frozenset({'negative_binomial'})),
				('covariate_list', frozenset({''})),
				('covariates', frozenset({'', '+ post:damage', '+ year:damage'})),
				('damage', frozenset({'log_dam', 'dam'})),
				('feminity', frozenset({'female', 'masfem'})),
				('outliers',
				frozenset({"c('Katrina')",
							"c('Katrina', 'Audrey')",
							"c('Katrina', 'Audrey', 'Sandy')",
							"c('Katrina', 'Audrey', 'Sandy', 'Andrew')",
							"c('Katrina', 'Audrey', 'Sandy', 'Andrew', 'Donna')",
							'c()'})),
				('predictor_list', frozenset({''})),
				('predictors',
				frozenset({'feminity + damage + pressure + feminity:damage + '
							'feminity:pressure',
							'feminity + damage + z3',
							'feminity + damage + z3 + feminity:damage + feminity:z3',
							'feminity + damage + zcat + feminity:damage + feminity:zcat',
							'feminity + damage + zwin + feminity:damage + feminity:zwin'})),
				('undo_transform', frozenset({'exp(value)'}))
			)
		"""
		return self._decisions_to_lines
	
	@property
	def common_lines(self) -> Dict[FrozenSet[int], List[str]]:
		"""
		Mapping from set of universe nums to lines of code in which all these universes share
		"""
		return self._common_lines
	@property
	def lines_to_decisions(self) -> Dict[str, Tuple[Tuple[str, FrozenSet[str]]]]:
		"""
		Mapping from line of code to the decisions and options which share this code
		"""
		return self._lines_to_decisions

	@unum_shared_lines.setter
	def unum_shared_lines(self, unum_shared_lines):
		self._unum_shared_lines = unum_shared_lines
  
	@decisions_to_lines.setter
	def decisions_to_lines(self, decisions_to_lines):
		self._decisions_to_lines = decisions_to_lines
  
	@common_lines.setter
	def common_lines(self, common_lines):
		self._common_lines = common_lines
  
	@lines_to_decisions.setter
	def lines_to_decisions(self, lines_to_decisions):
		self._lines_to_decisions = lines_to_decisions

class DebugMultiverse:
	def __init__(self, folder):
		self.folder = folder
		self.log_folder = os.path.join(folder, DIR_LOG)
		self.file_log = os.path.join(self.log_folder, 'logs.csv')
		self.code_folder = osp.join(folder, DIR_SCRIPT)
		self.summary_df = pd.read_csv(osp.join(self.folder, 'summary.csv')).fillna('')
		self.summary_df = set_universe_as_index(self.summary_df)
		self.decisions = get_decs(self.summary_df)
		fn = self.summary_df['Filename'].to_list()[0]
		try:
			with open(self.folder + '/lang.json', 'r') as f:
				self.lang = Lang(fn, supported_langs=json.load(f))
		except IOError:
			self.lang = Lang(fn)
		self._decisions = {k: frozenset(v) for k, v in self.decisions.items() if len(v) > 1}
		self.error_info = ErrorAggregateInfo({}, {}, {}, {})
		self.warning_info = ErrorAggregateInfo({}, {}, {}, {})
		self.refresh_vals()

	def refresh_vals(self):
		self.log_df, status = merge_error(self.log_folder, self.lang.lang[0])
		if len(self.log_df) > 0:
			error_msg_unique = self.log_df['error_msg'].unique()
			if not(len(error_msg_unique) == 1 and error_msg_unique[0] == ''):
				self.log_df['grped_error_msg'] = group_similar_strings(self.log_df['error_msg'], ignore_index=True) 
				error_to_uids: Dict[str, Set[int]] = self.log_df.groupby('grped_error_msg')['uid'].apply(frozenset).to_dict()
				self.error_info = self.init_debug_multiverse(error_to_uids) 
			

			self.log_df['warning_msgs'] = self.log_df['warning_msgs'].apply(lambda x: eval(x) if type(x) is str else x)
			warning_msgs = self.log_df[['uid', 'warning_msgs']].explode('warning_msgs').dropna()
			warning_msg_unique = warning_msgs['warning_msgs'].unique()
			if len(warning_msg_unique) != 0:
				warning_msgs['grped_warning_msg']= group_similar_strings(warning_msgs['warning_msgs'], ignore_index=True)
				warning_to_uids = warning_msgs.groupby('grped_warning_msg')['uid'].apply(frozenset).to_dict()
				self.warning_info = self.init_debug_multiverse(warning_to_uids)

	def get_error_info(self, is_warning=False) -> ErrorAggregateInfo:
		if is_warning:
			return self.warning_info
		else:
			return self.error_info
  
	def return_json_errors(self, is_warning=False):
		errors = []
		no_errors = []

		# previous merged error
		fn = osp.join(self.log_folder, 'errors.csv')
		if os.path.exists(fn):
			df = pd.read_csv(fn, na_filter=False)
			if len(df) < len(self.summary_df):
				self.refresh_vals()
		
		if not is_warning:
			error_info: ErrorAggregateInfo = self.error_info
			first_no_str_line = 'No Error but has Miscl Warnings'
		else:
			error_info: ErrorAggregateInfo = self.warning_info
			first_no_str_line = 'No Warnings but has Error'
  
		for unums, error_strs in error_info.common_lines.items():
			for error_str in error_strs:
				if error_str == '':
					first_line = first_no_str_line
					first_lines = ''
				else:
					first_line = error_str.split('\n')[0]
					if self.lang.lang[0] == 'python':
						if is_warning:
							pt = '[a-zA-z]*Warning:\s.*'
							m = re.search(pt, first_line)
							if m:
								first_line = m[0]
						else:
							first_line = error_str.split('\n')[-1].strip()
		
					if len(first_line) > 50:
						first_line = first_line[:47] + ' ...'
					first_lines = '\n'.join(error_str.split('\n')[:5]) + '\n...'

				common_decs = decisions_set_unique(error_info.lines_to_decisions[error_str], 
										self.orig_decisions)
				for dec, opts in common_decs.items():
					if dec == 'All Universes':
						break
					orig_opts = self.decisions[dec]
					opt_str = ''
					for i, opt in enumerate(orig_opts):
						if opt not in opts:
							opt_str += f'{i+1}. {opt} <br>'
						else:
							opt_str += f'<em><b>{i+1}.{opt}</b></em><br>'
					common_decs[dec] = opt_str
				common_unums = random.sample(list(unums), min(len(unums), 10))
				number_affected = f"{len(unums)} out of {len(self.summary_df)} Universes Affected"
				common_unums_jsons = []
				for unum in common_unums:
					df_row = self.summary_df.loc[unum]
					filename = osp.join(self.code_folder, df_row[0])
					decs = [{"decision": dec, "option": opt} 
							for dec, opt in df_row[1:].to_dict().items()]
					common_unums_jsons.append({
						"decisions": decs,
						"universe_path": filename,
						"universe_num": unum
					})
				if error_str == '':
					no_errors.append({
						"common_decs": common_decs,
						"error_msg": error_str,
						"error_msg_first_line": first_line,
						"error_msg_first_lines": first_lines,
						"common_universes": common_unums_jsons,
						"number_affected": number_affected
					})
				else:
					errors.append(
						{
						"common_decs": common_decs,
						"error_msg": error_str,
						"error_msg_first_line": first_line,
						"error_msg_first_lines": first_lines,
						"common_universes": sorted(common_unums_jsons, key=lambda x: x['universe_num']),
						"number_affected": number_affected
					})
		errors = sorted(errors, key=lambda x: int(x['number_affected'].split()[0]), reverse=True)
		return errors + no_errors
	
	@property
	def orig_decisions(self) -> Dict[str, FrozenSet[str]]:
		"""
		Mapping from decisions name to its decision options
		"""
		return self._decisions
	
	def init_debug_multiverse(self, error_to_uids:  Dict[str, Set[int]]):
		summary_df = self.summary_df
		def get_common_lines(res_lines: Dict[str, set]):
			new_res = defaultdict(list)
			for line, unum_set in res_lines.items():
				key = frozenset(unum_set)
				new_res[key].append(line)
			return new_res
		common_lines  = get_common_lines(error_to_uids)
		
		decisions_to_lines = defaultdict(list)
		for k, line in common_lines.items():
			subset_df = summary_df.loc[list(k)]
			decisions = {k: frozenset(v) for k, v in get_decs(subset_df).items()}
			decisions = {k: v for k, v in decisions.items() if k in self.orig_decisions}
			decisions_repr = tuple((k, decisions[k])for k in sorted(decisions.keys())) 
			decisions_to_lines[decisions_repr].extend(line)
		unum_shared_lines: Dict[int, Dict[str, Set[int]]] = defaultdict(dict)
		
		for k, lines in common_lines.items():
			for unum in k:
				shared_unums = set(k)
				shared_unums.discard(unum)
				for line in lines:
					unum_shared_lines[unum][line] = shared_unums

		lines_to_decisions = {line: k for k, v in decisions_to_lines.items() for line in v}
  
		return ErrorAggregateInfo(unum_shared_lines, decisions_to_lines, common_lines, lines_to_decisions)

	def print_common_universes(self, unum, is_warning=False):
		"""
		For a universe what are its error ouputs and what are some other sample universes associated with its error output
		"""
		error_info = self.get_error_info(is_warning)
		print(f'{bcolors.OKGREEN} ====== Universe {unum} Common Code Universes======')
		for lines, other_unums in error_info.unum_shared_lines[unum].items():
			print(f'{bcolors.OKBLUE}{lines}')
			print(f'{bcolors.OKGREEN}Shared unums: {random.sample(list(other_unums), 10)}')
			print(f'{bcolors.OKGREEN}Total shared: {len(other_unums)}\n\n')
		
	def print_common_output(self, unum1, unum2, is_warning=False):
		"""
		What are common error outputs between universe A and universe B
		"""
		error_info = self.get_error_info(is_warning)
		print(f'{bcolors.OKGREEN} ====== Universe {unum1} and {unum2} Common Code ======')
		for lines, other_nums in error_info.unum_shared_lines[unum1].items():
			if unum2 in other_nums:
				print(f'{bcolors.OKBLUE}{lines}')

	def print_decision_and_code(self, i=0, is_warning=False):
		"""
		What are some of the common error outputs and the associated decision with that error output
		"""
		error_info = self.get_error_info(is_warning)
		for ind, (k, lines) in enumerate(error_info.decisions_to_lines.items()):
			if ind == i:
				print(f'{bcolors.OKGREEN}======== Decisions ========{bcolors.OKGREEN}')
				print(frozen_set_to_str(k, self.orig_decisions))
				print(F'{bcolors.OKBLUE}======== Code ========{bcolors.OKBLUE}')
				print(f'\n\n'.join(lines))
		
	def print_common_decisions(self, unum, is_warning=False):
		"""
		For a universe what are the decisions associated with its error output
		What are also some other sample universes associated with its error output
		"""
		error_info = self.get_error_info(is_warning)
  
		print(f'{bcolors.OKGREEN}======== {unum} Code Decisions ========{bcolors.OKGREEN}')
		for lines, other_unums in error_info.unum_shared_lines[unum].items():
			decision = error_info.lines_to_decisions[lines]
			print(f'{bcolors.OKBLUE}====== Code ======{bcolors.OKBLUE}')
			print(lines)
			print(f'{bcolors.OKGREEN}====== Decisions ======{bcolors.OKGREEN}')
			print(f'{bcolors.OKGREEN}{frozen_set_to_str(decision, self.orig_decisions)}')
			print(f'{bcolors.OKGREEN}Sample shared unums: {random.sample(list(other_unums), 10)}')
			print(f'{bcolors.OKGREEN}Total shared: {len(other_unums)}\n\n')

	# TODO what are common decisions shared by two universes
def get_min_decisions(summary_df: pd.DataFrame):
	decision_options_dict: Dict[str, list] = {c: list(summary_df[c].unique())
												  for c in summary_df.columns[2:]}
	decision_options_dict = {k: set(v) for k, v in decision_options_dict.items() if len(v) > 1}
	summary_df = set_universe_as_index(summary_df)
	copy_df = deepcopy(summary_df)
	to_run = {}
	
	while len(copy_df) > 0 and any(len(v) > 0 for v in decision_options_dict.values()):
		row = copy_df.sample(1)
		to_run[row.index.values[0]] = {c: row[c].values[0] for c in row.columns[2:]}
		cols = [(c, copy_df[c].nunique()) 
				for c in copy_df.columns[2:] if copy_df[c].nunique() > 1]
		if len(cols) == 0:
			break
		max_col = sorted(cols, key=lambda x: x[1])[-1][0]
		for col, v in decision_options_dict.items():
			v.discard(row[col].values[0])  
		copy_df = copy_df.loc[copy_df[max_col] != row[max_col].values[0]]
		
	return to_run


def merge_error(dir_log, lang="r"):
	""" Merge the error logs into errors.csv """
	fn = join(dir_log, 'errors.csv')
	logs = []
	merged = []
	df = None
	# exit code
	if os.path.exists(osp.join(dir_log, 'logs.csv')):
		status = pd.read_csv(osp.join(dir_log, 'logs.csv'), index_col='uid')
		logs = status.index.tolist()

	# previous merged error
	# if os.path.exists(fn):
	# 	df = pd.read_csv(fn, na_filter=False)
	# 	merged = df['uid'].tolist()

	# these are the new logs
	remain = set(logs).difference(set(merged))
	res = []
	for f in tqdm(os.listdir(dir_log)):
		if f.startswith('error') and f.endswith('txt'):
			uid = int(os.path.splitext(f)[0].split('_')[1])
			if uid in remain:
				with open(os.path.join(dir_log, f), 'r') as fo:
					data = fo.read()
					code = status.loc[uid]['exit_code']
					res.append([uid, code, data])

	# cluster errors into groups
	res = pd.DataFrame(res, columns=['uid', 'exit_code', 'message'])
	res = cluster_error(res, lang)

	# save file and return
	df = res if df is None else pd.concat([df, res], ignore_index=True)
	df.to_csv(fn, index=False)
	return df, status

def cluster_error(df, lang="r"):
	""" Cluster the error messages based on heuristics """
	if df.shape[0] < 1:
		df['group'] = pd.Series(dtype=str)
		return df
	# regex
	if lang == 'r':
		pt_skip = r'^warning message'
		pt_err = r'^error'
		pt_halt = r'^execution halted'
	
	else:
		pt_skip = '^(/[a-zA-Z0-9._-]+)+[a-zA-Z0-9._-]*.py:[0-9]+:\s?[a-zA-z]*Warning'
		pt_err = r'^traceback \(most recent call last\):'
		pt_halt = '^([\w.]+Error|[\w*.]exception)'
  
	# row-wise function
	def process_row (row):
		sentences = row['message'].split('\n')
		i = 0

		is_warning = lambda sent: re.search(pt_skip, sent, flags=re.IGNORECASE) is not None
		is_error = lambda sent: re.search(pt_err, sent, flags=re.IGNORECASE) is not None
		is_execution_halt = lambda sent: re.search(pt_halt, sent, flags=re.IGNORECASE) is not None
		warning_msgs = []
		finished_w_warnings = False
		while i < len(sentences):
			# skip the rows with uninformative message, and group by the first row
			sent = sentences[i]
			if is_error(sent):
				break
			if is_warning(sent):
				warning_msg = [sentences[i]]
				i += 1
				while i < len(sentences) and not is_warning(sentences[i]):
					if is_error(sentences[i]):
						finished_w_warnings = True
						break
					warning_msg.append(sentences[i])
					i += 1
				warning_msgs.append('\n'.join(warning_msg))
			if finished_w_warnings:
				break
			i += 1
		# look for 'error' if the exit code is non-zero
		error_msg = []
		if row['exit_code'] > 0:
			while i < len(sentences): # start from where we left off
				if is_error(sentences[i]):
					error_msg = [sentences[i]]
					i += 1
					while i < len(sentences) and not is_execution_halt(sentences[i]):
						error_msg.append(sentences[i])
						i += 1
					if i < len(sentences):
						error_msg.append(sentences[i])
					break
				i += 1
		return warning_msgs, '\n'.join(error_msg)
	df['warning_msgs'], df['error_msg'] = zip(*df.apply(process_row, axis=1))
	return df
		
if __name__ == '__main__':
	from os.path import join
	MULTIVERSE_FOLDER = "/Users/qikungu/PythonProjects/MultiverseTooling/user_study/08282022_Bernease/hurricane_bug_all"
	LOG_FOLDER = join(MULTIVERSE_FOLDER, 'multiverse', 'boba_logs')
	SUM_DF_PATH = join(MULTIVERSE_FOLDER, 'multiverse', 'summary.csv')
	
	# merge_error(LOG_FOLDER)
	df = pd.read_csv(SUM_DF_PATH)
	min_decs = get_min_decisions(df)
	print(f'{bcolors.OKCYAN}====== Sampled Universes to Run ======')
	pprint(min_decs)
	debug_multiverse = DebugMultiverse(join(MULTIVERSE_FOLDER, 'multiverse'))
	res = debug_multiverse.return_json_errors(is_warning=True)
	debug_multiverse.print_common_decisions(768)
	debug_multiverse.print_common_output(768, 532)
	debug_multiverse.print_decision_and_code(2)
	print('here')