/*
 *  elm_sql_scrape.cpp
 *
 *  Copyright 2007-2013 Jeffrey Newman
 *
 *  This file is part of ELM.
 *  
 *  ELM is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *  
 *  ELM is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *  
 *  You should have received a copy of the GNU General Public License
 *  along with ELM.  If not, see <http://www.gnu.org/licenses/>.
 *  
 */

#include <iostream>

#include <cstring>
#include "etk.h"
#include "etk_refcount.h"
#include "elm_sql_facet.h"
#include "elm_datamatrix.h"
#include "elm_cellcode.h"
#include "elm_vascular.h"

using namespace std;
using namespace etk;


elm::datamatrix elm::datamatrix_t::pointer()
{
	return myself.lock();
}



long elm::datamatrix_t::refcount()
{
	if (myself.expired()) {
		OOPS("pointer expired");
	}
	datamatrix t = myself.lock();
	return t.use_count();
}

elm::datamatrix elm::datamatrix_t::create(dimensionality dim, matrix_dtype tp, matrix_purpose purp)
{
	elm::datamatrix p = boosted::make_shared<datamatrix_t>(dim,tp,purp);
	p->myself = p;
	return p;
}

elm::datamatrix elm::datamatrix_t::copy() const
{
	elm::datamatrix p = create(dimty, dtype, dpurp);

	p->_VarNames    =_VarNames;
	p->_repository = _repository;
	p->_casedex    = _casedex;

	return p;
}


elm::datamatrix_t::datamatrix_t(dimensionality dim, matrix_dtype tp, matrix_purpose purp)
: dimty          (dim)
, dtype          (tp)
, dpurp          (purp)
, _repository    ()
, _VarNames      ()
, _repo_lock     (etk::reading_lockout::open())
, _casedex       (nullptr)
{
}

elm::datamatrix_t::datamatrix_t(const elm::datamatrix_t& x)
: dimty          (x.dimty)
, dtype          (x.dtype)
, _repository    ()
, _VarNames      (x._VarNames)
, _repo_lock     (etk::reading_lockout::open())
, _casedex       (x._casedex)
{
	_repository = x._repository;
}

elm::datamatrix_t::datamatrix_t()
: dimty          ()
, dtype          ()
, _repository    ()
, _VarNames      ()
, _repo_lock     (etk::reading_lockout::open())
, _casedex       (nullptr)
{
	OOPS("do not create datamatrix_t directly, use create() or a read_* method");
}


elm::datamatrix_t::~datamatrix_t()
{
	tearDown(true);
}




void elm::datamatrix_t::tearDown(bool force)
{
	if (!force) {
		if (_repo_lock->check()) {
			OOPS("There is a repository read lock active, it is not safe to tearDown");
		}
	}
	_repository.destroy();
}



void elm::datamatrix_t::set_variables( const std::vector<std::string>& varnames )
{
	if (dimty==case_var && varnames.size()!=_repository.size2()) {
		OOPS("Must set exactly ",_repository.size2()," variable names, you gave ",varnames.size(),".");
	}
	if (dimty==case_alt_var && varnames.size()!=_repository.size3()) {
		OOPS("Must set exactly ",_repository.size3()," variable names, you gave ",varnames.size(),".");
	}

	_VarNames.clear();

	std::vector<std::string>::const_iterator x;
	for (x = varnames.begin(); x != varnames.end(); x++) {
		_VarNames.push_back(*x);
	}
}

const std::vector<std::string>& elm::datamatrix_t::get_variables() const
{
	return _VarNames;
}

size_t elm::datamatrix_t::nVars() const
{
	if (dimty==case_var && _VarNames.size()!=_repository.size2()) {
		OOPS("There are ",_repository.size2()," variables, and ",_VarNames.size()," names.");
	}
	if (dimty==case_alt_var && _VarNames.size()!=_repository.size3()) {
		OOPS("There are ",_repository.size3()," variables, and ",_VarNames.size()," names.");
	}
	return _VarNames.size();
}

size_t elm::datamatrix_t::nAlts() const
{
	if (dimty==case_var) {
		return 0;
	}
	if (dimty==case_alt_var) {
		return _repository.size2();
	}
	return 0;
}

size_t elm::datamatrix_t::nCases() const
{
	if (_casedex && _casedex->size()!=_repository.size1()) {
		OOPS("There are ",_casedex->size()," cases in the index, and ",_repository.size1()," rows in the datamatrix.");
	}
	return _repository.size1();
}



etk::ptr_lockout<const double> elm::datamatrix_t::values(const unsigned& firstcasenum, const size_t& numberofcases)
{
	return ptr_lockout<const double>(_repository.ptr(firstcasenum), _repo_lock);
}

etk::ptr_lockout<const bool> elm::datamatrix_t::boolvalues(const unsigned& firstcasenum, const size_t& numberofcases)
{
	return ptr_lockout<const bool>(_repository.ptr_bool(firstcasenum), _repo_lock);
}

etk::ptr_lockout<const double> elm::datamatrix_t::values(const unsigned& firstcasenum, const size_t& numberofcases) const
{
	return ptr_lockout<const double>(_repository.ptr(firstcasenum), const_cast<elm::datamatrix_t*>(this)->_repo_lock);
}

etk::ptr_lockout<const bool> elm::datamatrix_t::boolvalues(const unsigned& firstcasenum, const size_t& numberofcases) const
{
	return ptr_lockout<const bool>(_repository.ptr_bool(firstcasenum), const_cast<elm::datamatrix_t*>(this)->_repo_lock);
}


double elm::datamatrix_t::value(const unsigned& c, const unsigned& a, const unsigned& v) const
{
	return *(values(c,1)+(a*nVars())+v);
}

double elm::datamatrix_t::value(const unsigned& c, const unsigned& v) const
{
	return *(values(c,1)+v);
}

bool elm::datamatrix_t::boolvalue(const unsigned& c, const unsigned& a, const unsigned& v) const
{
	return *(boolvalues(c,1)+(a*nVars())+v);
}
bool elm::datamatrix_t::boolvalue(const unsigned& c, const unsigned& v) const
{
	return *(boolvalues(c,1)+v);
}


// STYLES
#define IDCO   0x01
#define IDCA   0x02
#define CHOO   0x10
#define WGHT   0x20
#define AVAL   0x40


//elm::datamatrix elm::datamatrix_t::create_idca(elm::Facet* db, const std::vector<std::string>& varnames)
//{
//	elm::datamatrix x = elm::datamatrix_t::create(case_alt_var, mtrx_double, purp_vars);
//	x->read_from_facet(db, IDCA, &varnames);
//	return x;
//}
//
//elm::datamatrix elm::datamatrix_t::create_idco(elm::Facet* db, const std::vector<std::string>& varnames)
//{
//	elm::datamatrix x = elm::datamatrix_t::create(case_var, mtrx_double, purp_vars);
//	x->read_from_facet(db, IDCO, &varnames);
//	return x;
//}
//
//elm::datamatrix elm::datamatrix_t::create_choo(elm::Facet* db)
//{
//	elm::datamatrix x = elm::datamatrix_t::create(case_alt_var, mtrx_double, purp_choice);
//	x->read_from_facet(db, CHOO);
//	return x;
//}
//
//elm::datamatrix elm::datamatrix_t::create_wght(elm::Facet* db)
//{
//	elm::datamatrix x = elm::datamatrix_t::create(case_var, mtrx_double, purp_weight);
//	x->read_from_facet(db, WGHT);
//	return x;
//}
//
//elm::datamatrix elm::datamatrix_t::create_aval(elm::Facet* db)
//{
//	elm::datamatrix x = elm::datamatrix_t::create(case_alt_var, mtrx_bool, purp_avail);
//	x->read_from_facet(db, AVAL);
//	return x;
//}









elm::datamatrix elm::datamatrix_t::read_idca(elm::Facet* db, const std::vector<std::string>& varnames, long long* caseid)
{
	elm::datamatrix x = elm::datamatrix_t::create(case_alt_var, mtrx_double, purp_vars);
	x->read_from_facet(db, IDCA, &varnames, caseid);
	return x;
}

elm::datamatrix elm::datamatrix_t::read_idco(elm::Facet* db, const std::vector<std::string>& varnames, long long* caseid)
{
	elm::datamatrix x = elm::datamatrix_t::create(case_var, mtrx_double, purp_vars);
	x->read_from_facet(db, IDCO, &varnames, caseid);
	return x;
}

elm::datamatrix elm::datamatrix_t::read_choo(elm::Facet* db, long long* caseid)
{
	elm::datamatrix x = elm::datamatrix_t::create(case_alt_var, mtrx_double, purp_choice);
	x->read_from_facet(db, CHOO, nullptr, caseid);
	return x;
}

elm::datamatrix elm::datamatrix_t::read_wght(elm::Facet* db, long long* caseid)
{
	elm::datamatrix x = elm::datamatrix_t::create(case_var, mtrx_double, purp_weight);
	x->read_from_facet(db, WGHT, nullptr, caseid);
	return x;
}

elm::datamatrix elm::datamatrix_t::read_aval(elm::Facet* db, long long* caseid)
{
	elm::datamatrix x = elm::datamatrix_t::create(case_alt_var, mtrx_bool, purp_avail);
	x->read_from_facet(db, AVAL, nullptr, caseid);
	return x;
}









void elm::datamatrix_t::read_from_facet(elm::Facet* db, int style, const std::vector<std::string>* varnames, long long* caseid)
{
	
	std::vector<std::string>* temp_varnames = new std::vector<std::string>;
	if (!varnames) varnames = temp_varnames;
	
	size_t cs = db->nCases();
	if (caseid) {
		cs = 1;
	}
	
	size_t nV = varnames->size();

	if (style&(CHOO|AVAL|WGHT)) {
		nV = 1;
	}
		
	if (_repo_lock->check()) {
		OOPS("There is a repository read lock active, cannot load new data now");
	}
	
		
	cellcodeset bad_codes;
	
	if (style&IDCA) {
		_repository.resize(cs,db->nAlts(),nV);
		_VarNames = *varnames;
	} else if (style&IDCO) {
		_repository.resize(cs,nV);
		_VarNames = *varnames;
	} else if (style&CHOO) {
		_repository.resize(cs,db->nAlts(),1);
		_VarNames.clear();
		_VarNames.push_back("choice");
	} else if (style&AVAL) {
		_repository.resize_bool(cs,db->nAlts(),1);
		_VarNames.clear();
		_VarNames.push_back("avail");
	} else if (style&WGHT) {
		_repository.resize(cs,1);
		_VarNames.clear();
		_VarNames.push_back("weight");
	} else {
		OOPS("Unknown datamatrix_t style ",style);
	}
	_repository.initialize(0.0);
	
	
	const VAS_Cell* alt;
	cellcode alt_code;
	long long current_caseid;
	size_t c = 0;
	
	SQLiteStmtPtr _stmt = db->sql_statement_readonly("");
	
	if (style&IDCA) {
		_stmt->prepare( db->query_idca(*varnames,false,caseid) );
	} else if (style&IDCO) {
		_stmt->prepare( db->query_idco(*varnames,false,caseid) );
	} else if (style&CHOO) {
		_stmt->prepare( db->query_choice(caseid) );
	} else if (style&AVAL) {
		if (db->all_alts_always_available()) {
			_repository.bool_initialize(true);
			return;
		}
		_stmt->prepare( db->query_avail(caseid) );
	} else if (style&WGHT) {
		_stmt->prepare( db->query_weight(caseid) );
	}
	
	MONITOR(db->msg) << "SQL: "<< _stmt->sql() ;
	std::string the_stmt = _stmt->sql();
	
	clock_t prevmsgtime = clock();
	clock_t timenow;
	
	_stmt->execute();
	if (_stmt->status()==SQLITE_ROW) {
		current_caseid = _stmt->getInt(0);
	}
	while (_stmt->status()==SQLITE_ROW) {
		try {
			if (current_caseid != _stmt->getInt64(0)) {
				c++;
				current_caseid = _stmt->getInt64(0);
			}
			timenow = clock();
			if (timenow > prevmsgtime + (CLOCKS_PER_SEC * 3)) {
				MONITOR(db->msg) << "reading case "<< current_caseid << ", " << 100.0*double(c)/double(cs) << "% ..." ;
				prevmsgtime = clock();
			}
		}
		SPOO {
			_stmt->execute();
			continue;
		}
		if (style&(IDCA|AVAL|CHOO)) {
			alt_code = _stmt->getInt64(1);
			if (alt_code==0) {
				bad_codes.insert(alt_code);
				_stmt->execute();
				continue;
			}
			try {
				alt = db->DataDNA(current_caseid)->cell_from_code(alt_code);
			} SPOO {
				bad_codes.insert(alt_code);
				_stmt->execute();
				continue;
			}
			if (dtype==mtrx_bool) {
				_stmt->getBools (2, 2+nVars(),_repository.ptr_bool(c,alt->slot()));
			} else if (dtype==mtrx_double) {
				_stmt->getDoubles (2, 2+nVars(),_repository.ptr(c,alt->slot()));
			} else if (dtype==mtrx_int64) {
				OOPS("incompatible dtype for datamatrix (int64 not implemented)");
			} else {
				OOPS("incompatible dtype for datamatrix");
			}
		} else if (style&(IDCO|WGHT)) {
			if (dtype==mtrx_bool) {
				_stmt->getBools (1, 1+nVars(),_repository.ptr_bool(c));
			} else if (dtype==mtrx_double) {
				_stmt->getDoubles (1, 1+nVars(),_repository.ptr(c));
			} else {
				OOPS("incompatible dtype for datamatrix (int64 not implemented)");
			}
		}
		_stmt->execute();
	}
	MONITOR(db->msg) << "table read end" ;
	if (bad_codes.size()) {
		ostringstream badness;
		badness << "while reading data ( " << _stmt->sql() << " ) there are " << bad_codes.size() << " unidentified cell codes:\n";
		for (std::set<cellcode>::iterator b=bad_codes.begin(); b!=bad_codes.end(); b++)
			badness << *b << "\n";
		OOPS(badness.str());
	}
	
	delete temp_varnames;
}


/*
void elm::datamatrix_t::load_values(const size_t& firstcasenum, const size_t& numberofcases)
{
	if (firstcasenum==0 && numberofcases==0 && fully_loaded()) {
		return;
	}
	
	if (firstcasenum!=0 || numberofcases!=0) {
		if (is_loaded_in_range(firstcasenum,numberofcases)) {
			return;
		}
	}
	
	size_t cs = numberofcases;
	if (numberofcases==0) cs = parent->nCases();
	if (firstcasenum+numberofcases>parent->nCases()) cs = parent->nCases() - firstcasenum;

	if (_style&(CHOO|AVAL|WGHT)) _nVars_ = 1;

	if (_style&IDCA) {
		if (cs==0 || parent->nAlts()==0 || nVars()==0) return;
	} else if (_style&IDCO) {
		if (cs==0 || nVars()==0) return;
	}

	if (_repo_lock->check()) {
		OOPS("There is a repository read lock active, cannot load new data now\n", describe_loaded_range(),
			 "\nAsking for case ",firstcasenum, " to case ", firstcasenum+numberofcases);
	}
	if (_bool_lock->check()) {
		OOPS("There is a bool read lock active, cannot load new data now\n", describe_loaded_range(),
			 "\nAsking for case ",firstcasenum, " to case ", firstcasenum+numberofcases);
	}
		

	if (_as_bool()) {
		if ((firstcasenum>=_firstcasenum)&&(firstcasenum+cs<=_firstcasenum+_numberofcases)&&(_bools.size()>=cs)) return;
		_repository.destroy();
	} else {
		if ((firstcasenum>=_firstcasenum)&&(firstcasenum+cs<=_firstcasenum+_numberofcases)&&(_repository.size()>=cs)) return;
		_bools.destroy();
	}
	
	cellcodeset bad_codes;
		
	if (_style&IDCA) {
		if (cs==0 || parent->nAlts()==0 || nVars()==0) return;
		_repository.resize(cs,parent->nAlts(),nVars());
	} else if (_style&IDCO) {
		if (cs==0 || nVars()==0) return;
		_repository.resize(cs,nVars());
	} else if (_style&CHOO) {
		_repository.resize(cs,parent->nAlts(),1);
	} else if (_style&AVAL) {
		_bools.resize(cs,parent->nAlts(),1);
	} else if (_style&WGHT) {
		_repository.resize(cs,1);
	} else {
		OOPS("Unknown datamatrix_t style ",_style);
	}
	if (_as_bool()) {
		_bools.initialize(false);
	} else {
		_repository.initialize(0.0);
	}
	
	if (nVars()==0 || cs<=0) return;


	const VAS_Cell* alt;
	cellcode alt_code;
	long long current_caseid;
	size_t c = 0;
	
	if (_style&IDCA) { 
		_stmt->prepare( parent->query_idca(_VarNames,firstcasenum,cs) );
	} else if (_style&IDCO) {
		_stmt->prepare( parent->query_idco(_VarNames,firstcasenum,cs) );
	} else if (_style&CHOO) {
		_stmt->prepare( parent->query_choice(firstcasenum,cs) );
	} else if (_style&AVAL) {
		_stmt->prepare( parent->query_avail(firstcasenum,cs) );
	} else if (_style&WGHT) {
		_stmt->prepare( parent->query_weight(firstcasenum,cs) );
	}
		
	MONITOR(parent->msg) << "SQL: "<< _stmt->sql() ;
	std::string the_stmt = _stmt->sql();

	clock_t prevmsgtime = clock();
	clock_t timenow;
	
	_stmt->execute();
	if (_stmt->status()==SQLITE_ROW) {
		current_caseid = _stmt->getInt(0);
	}
	while (_stmt->status()==SQLITE_ROW) {
		try { 
			if (current_caseid != _stmt->getInt64(0)) {
				c++;
				current_caseid = _stmt->getInt64(0);
			}
			timenow = clock();
			if (timenow > prevmsgtime + (CLOCKS_PER_SEC * 3)) {
				MONITOR(parent->msg) << "reading case "<< current_caseid << ", " << 100.0*double(c)/double(cs) << "% ..." ;
				prevmsgtime = clock();
			}
		}
		SPOO {
			_stmt->execute();
			continue;
		}
		if (_style&(IDCA|AVAL|CHOO)) {
			alt_code = _stmt->getInt64(1);
			if (alt_code==0) {
				bad_codes.insert(alt_code);
				_stmt->execute();
				continue;
			}
			try { 
				alt = parent->DataDNA(current_caseid)->cell_from_code(alt_code);
			} SPOO {
				bad_codes.insert(alt_code);
				_stmt->execute();
				continue;
			}
			if (_as_bool()) {
				_stmt->getBools (2, 2+nVars(),_bools.ptr(c,alt->slot()));
			} else {
				_stmt->getDoubles (2, 2+nVars(),_repository.ptr(c,alt->slot()));
			}
		} else if (_style&(IDCO|WGHT)) {
			if (_as_bool()) {
				_stmt->getBools (1, 1+nVars(),_bools.ptr(c));
			} else {
				_stmt->getDoubles (1, 1+nVars(),_repository.ptr(c));
			}
		}
		_stmt->execute();
	}
	MONITOR(parent->msg) << "table read end" ;
	if (bad_codes.size()) {
		ostringstream badness;
		badness << "while reading data ( " << _stmt->sql() << " ) there are " << bad_codes.size() << " unidentified cell codes:\n";
		for (std::set<cellcode>::iterator b=bad_codes.begin(); b!=bad_codes.end(); b++)
			badness << *b << "\n"; 
		OOPS(badness.str());
	}
	_firstcasenum = firstcasenum;
	_numberofcases = cs;
}
*/



std::string elm::datamatrix_t::printcase(const unsigned& r) const
{
	std::ostringstream ret;
	unsigned x2, x3;
	char depMarker, colMarker, rowMarker;
	if (dimty==case_var && dtype==mtrx_double) {
		depMarker = ' ';
		colMarker = '\t';
		rowMarker = '\n';
		for ( x2=0; x2<nVars(); x2++ ) { 
			ret << value(r,x2) << colMarker;
		}
		ret << rowMarker;
	} else if (dimty==case_alt_var && dtype==mtrx_double) {
		depMarker = '\t';
		colMarker = '\n';
		rowMarker = '\n';
		for ( x2=0; x2<nAlts(); x2++ ) { 
			for ( x3=0; x3<nVars(); x3++ ) { 
				ret << value(r,x2,x3) << depMarker;
			}
			ret << colMarker;
		}
		ret << rowMarker;
	}
	return ret.str();
}

std::string elm::datamatrix_t::printcases(unsigned rstart, const unsigned& rfinish) const
{
	std::ostringstream ret;
	for (; rstart < rfinish; rstart++) {
		ret << printcase(rstart);
	}
	return ret.str();
}


std::string elm::datamatrix_t::printboolcase(const unsigned& r) const
{
	std::ostringstream ret;
	unsigned x2, x3;
	char depMarker, colMarker, rowMarker;
	if (dimty==case_var && dtype==mtrx_bool) {
		depMarker = ' ';
		colMarker = '\t';
		rowMarker = '\n';
		for ( x2=0; x2<nVars(); x2++ ) { 
			ret << boolvalue(r,x2) << colMarker;
		}
		ret << rowMarker;
	} else if (dimty==case_alt_var && dtype==mtrx_bool) {
		depMarker = '\t';
		colMarker = '\n';
		rowMarker = '\n';
		for ( x2=0; x2<nAlts(); x2++ ) { 
			for ( x3=0; x3<nVars(); x3++ ) { 
				ret << boolvalue(r,x2,x3) << depMarker;
			}
			ret << colMarker;
		}
		ret << rowMarker;
	}
	return ret.str();
}

std::string elm::datamatrix_t::printboolcases(unsigned rstart, const unsigned& rfinish) const
{
	std::ostringstream ret;
	for (; rstart < rfinish; rstart++) {
		ret << printboolcase(rstart);
	}
	return ret.str();
}





void elm::datamatrix_t::ExportData (double* ExportTo, const unsigned& c, const unsigned& a, const unsigned& numberOfAlts) const
{
	if (dimty==case_alt_var) {
		cblas_dcopy(nVars(),values(c,1)+(a*nVars()),1,ExportTo,1);
		ExportTo+=nVars();
	} else if (dimty==case_var) {
		memset(ExportTo,0,nVars()*numberOfAlts*sizeof(double));
		cblas_dcopy(nVars(),values(c,1),1,ExportTo+a,numberOfAlts);
	}
}
void elm::datamatrix_t::ExportData	(double* ExportTo, const unsigned& c, const unsigned& a, const double& scale, const unsigned& numberOfAlts) const
{
	if (dimty==case_alt_var) {
		cblas_dcopy(nVars(),values(c,1)+(a*nVars()),1,ExportTo,1);
		cblas_dscal(nVars(), scale, ExportTo,1);
		ExportTo+=nVars();
	} else if (dimty==case_var) {
		memset(ExportTo,0,(nVars()*numberOfAlts)*sizeof(double));
		cblas_dcopy(nVars(),values(c,1),1,ExportTo+a,numberOfAlts);
		cblas_dscal(nVars(), scale, ExportTo+a,numberOfAlts);
		ExportTo+=(nVars()*numberOfAlts);
	}
}

void elm::datamatrix_t::OverlayData(double* ExportTo, const unsigned& c, const unsigned& a, const double& scale, const unsigned& numberOfAlts) const
{
	if (dimty==case_alt_var) {
		cblas_daxpy(nVars(),scale,values(c,1)+(a*nVars()),1,ExportTo,1);
		ExportTo+=nVars();
	} else if (dimty==case_var) {
		cblas_daxpy(nVars(),scale,values(c,1),1,ExportTo+a,numberOfAlts);
		ExportTo+=(nVars()*numberOfAlts);
	}		
}

PyObject* elm::datamatrix_t::getArray()
{
	PyObject* x = _repository.get_object();
	return x;
}


std::string elm::datamatrix_t::__str__() const
{
	std::ostringstream s;
	s << "larch.datamatrix";
	
	if (dimty==case_alt_var) {
		s << " [cav]";
	} else if (dimty==case_var) {
		s << " [cv]";
	} else {
		s << " [?dimty?]";
	}
	
	if (dtype==mtrx_double) {
		s << " dtype=double";
	} else if (dtype==mtrx_int64) {
		s << " dtype=int64";
	} else if (dtype==mtrx_bool) {
		s << " dtype=bool";
	} else {
		s << " dtype=?";
	}

	s << " (";
	try {
		s<< nCases();
	} SPOO {
		s << "ERR";
	}
	
	s<<"x";
	if (dimty==case_alt_var) {
		try {
			s << nAlts();
		} SPOO {
			s << "ERR";
		}
		
		s<<"x";
	}
	try {
		s << nVars();
	} SPOO {
		s << "ERR";
	}
	s << ")";

	auto v=_VarNames.begin();
	if (v!=_VarNames.end()) {
		s << " {";
		s << *v;
		v++;
		while (v!=_VarNames.end()) {
			s << ","<<*v;
			v++;
		}
		s << "}";
	}
	
	s << "";
	return s.str();
}

std::string elm::datamatrix_t::__repr__() const
{
	std::ostringstream s;
	s << "<larch.datamatrix";
	
	if (dimty==case_alt_var) {
		s << "[cav]";
	} else if (dimty==case_var) {
		s << "[cv]";
	} else {
		s << "[?dimty?]";
	}
	
	if (dtype==mtrx_double) {
		s << " dtype=double";
	} else if (dtype==mtrx_int64) {
		s << " dtype=int64";
	} else if (dtype==mtrx_bool) {
		s << " dtype=bool";
	} else {
		s << " dtype=?";
	}
	
	s << " (";
	try {
		s<< nCases();
	} SPOO {
		s << "ERR";
	}
	
	s<<"x";
	if (dimty==case_alt_var) {
		try {
			s << nAlts();
		} SPOO {
			s << "ERR";
		}
		
		s<<"x";
	}
	try {
		s << nVars();
	} SPOO {
		s << "ERR";
	}
	s << ")";
	
	s << ">";
	return s.str();
}



