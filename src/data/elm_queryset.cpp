//
//  elm_sql_queryset.cpp
//  Hangman
//
//  Created by Jeffrey Newman on 4/24/14.
//  Copyright (c) 2014 Jeffrey Newman. All rights reserved.
//

#include <Python.h>
#include "elm_queryset.h"

#include "etk_exception.h"

elm::QuerySet::~QuerySet()
{
	
}


elm::QuerySet::QuerySet(elm::Facet* validator)
: validator (validator)
{
	
}


void elm::QuerySet::set_validator(elm::Facet* validator)
{
	this->validator = validator;
}



std::string elm::QuerySet::__repr__() const
{
	return "<larch.core.QuerySet>";
}

std::string elm::QuerySet::actual_type() const
{
	return "QuerySet";
}



std::string elm::QuerySet::qry_idco   () const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_idca   () const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_idco_  () const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_idca_  () const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_alts   () const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_caseids() const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_choice () const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_weight () const
{
	return "QuerySet is an abstract base class, use a derived class";
}
std::string elm::QuerySet::qry_avail  () const
{
	return "QuerySet is an abstract base class, use a derived class";
}

bool elm::QuerySet::unweighted() const
{
	return false;
}
bool elm::QuerySet::all_alts_always_available() const
{
	return false;
}



PyObject* elm::QuerySet::pickled  () const
{
	Py_RETURN_NONE;
}






std::string elm::QuerySet::tbl_idco   () const
{
	return "("+qry_idco()+") AS elm_idco";
}

std::string elm::QuerySet::tbl_idca   () const
{
	return "("+qry_idca()+") AS elm_idca";
}

std::string elm::QuerySet::tbl_alts   () const
{
	return "("+qry_alts()+") AS elm_alternatives";
}

std::string elm::QuerySet::tbl_caseids() const
{
	return "("+qry_caseids()+") AS elm_caseids";
}

std::string elm::QuerySet::tbl_choice () const
{
	return "("+qry_choice()+") AS elm_choice";
}

std::string elm::QuerySet::tbl_weight () const
{
	return "("+qry_weight()+") AS elm_weight";
}

std::string elm::QuerySet::tbl_avail  () const
{
	if (qry_avail()=="") {
		OOPS("empty avail query");
	}

	return "("+qry_avail()+") AS elm_avail";
}



