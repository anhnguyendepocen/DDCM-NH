/*
This do-file saves a data of income by year after RA

The data is used in the reduced-form estimation and for recovering income
information for sample_model.do

*/


global databases "/mnt/Research/nealresearch/new-hope-secure/newhopemount/Data/databases"
global codes "/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes"
global results "/mnt/Research/nealresearch/new-hope-secure/newhopemount/results"



clear
clear matrix
clear mata
scalar drop _all
set more off
set maxvar 15000



*Use the CFS study
use "$databases/CFS_original.dta", clear
qui: do "$codes/data_cfs.do"


keep sampleid p_assign p_radatr cstartm curremp c1 piinvyy epiinvyy /*
*/ern*q* sup*q* csjm9* /*UI earnings, NH supplement, CSJ's
*/ kid*daty  c53d_1 piq93e epi74e /*kids at baseline and births
*/ c53d_3 /*Year of birth*/



**********************************
*CSJ: quarters in calendar time
**********************************

*Renaming CSJ calendar-time variables
forvalues y=94/97{

	local m=1
	foreach month in "01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12"{
		rename csjm`y'`month' csj19`y'm`m'
		local m=`m'+1
	}
	
} 


*Quarters

forvalues y=1994/1997{

	local m1=1
	forvalues q=1/4{
		local m2=`m1'+1
		local m3=`m2'+1
		egen csj`y'q`q'=rowtotal(csj`y'm`m1' csj`y'm`m2' csj`y'm`m3')
		local m1=`m3'+1
	}

}

****************************************
*UI Earnings: quarters in calendar time
****************************************



*Renaming 
rename ern4q93 ern1993q4

local nn=1
forvalues y=94/99{
	forvalues q=1/4{

		rename ern`q'q`y' ern19`y'q`q'
		
	}
}

local yy=0
forvalues y=2000/2003{
	forvalues q=1/4{

		rename ern`q'q0`yy' ern200`yy'q`q' 
				
	}

local yy=`yy'+1
}

*I DON"T HAVE EARNINGS FOR 98Q1: leave them as missing.
destring ern1998q1, replace force

*****************************************
*NH supplement: quarters in calendar time
*****************************************
destring sup*q*, replace force

*Renaming 
local nn=1
forvalues y=94/99{
	forvalues q=1/4{
		
		replace sup`y'q`q'=0 if sup`y'q`q'==.
		rename sup`y'q`q' sup19`y'q`q'
		
	}
}


forvalues q=1/4{
	replace sup00q`q'=0 if sup00q`q'==.
	rename sup00q`q' sup2000q`q' 
				
}

****Employment ****

forvalues y=1994/2003{
	forvalues q=1/4{
	
		if `y'<=1997{
			gen d_emp`y'q`q'=(ern`y'q`q'!=. & ern`y'q`q'>0) | (csj`y'q`q'!=. & csj`y'q`q'>0) 
		}
		else{
			gen d_emp`y'q`q'=(ern`y'q`q'!=. & ern`y'q`q'>0)
		}
	
	}

}

*Annual employment (proportion of employment)
forvalues y=1994/2003{

	if `y'==1998{
		egen employment_y`y'=rowmean(d_emp`y'q2 d_emp`y'q3 d_emp`y'q4)
	}
	else{
		egen employment_y`y'=rowmean(d_emp`y'q1 d_emp`y'q2 d_emp`y'q3 d_emp`y'q4)
	}

}



*****Annual income******
/*
Note: Rowmean(q1 q2 a3 q4)*4: the same as rowtotal, except for 1998, where I have no information on earnings

*/

forvalues y=1994/2003{
	
	*Earnings
	if `y'==1998{
	egen earn_y`y'=rowmean(ern`y'q2 ern`y'q3 ern`y'q4)
	}
	else{
	egen earn_y`y'=rowmean(ern`y'q1 ern`y'q2 ern`y'q3 ern`y'q4)
	}
	replace earn_y`y'=earn_y`y'*4
	
	*NH supplements
	if `y'<=2000{
		egen sup_y`y'=rowmean(sup`y'q1 sup`y'q2 sup`y'q3 sup`y'q4)
		replace sup_y`y'=sup_y`y'*4
	
	}
	
	*CSJ earnings
	if `y'<=1997{
		egen csj_y`y'=rowmean(csj`y'q1 csj`y'q2 csj`y'q3 csj`y'q4)
		replace csj_y`y'=csj_y`y'
	}

}

*Gross income (to compute EITC amounts. does not have NH supplements)
forvalues y=1994/2003{
	
	if `y'<=1997{
		egen gross_y`y'=rowtotal(earn_y`y' csj_y`y')
	
	}
	else{
		gen gross_y`y'=earn_y`y'
	}

}

*Employment by year

*****************************************
*Predicting the EITC
*****************************************

*Hoy many children?
*If didn't answer survey, assume they didn't have children

destring kid*daty, force replace
gen nkids_baseline=0

forvalues x=1/7{

	replace nkids_baseline=nkids_baseline+1 if kid`x'daty!=.
}

*Kids at year 2 (1996-1997)
rename nkids_baseline nkids_year0
gen nkids_year2=nkids_year0
replace nkids_year2=nkids_year2+1 if c53d_1=="1"

*Kids at year 5 (1999-2000)
gen nkids_year5=nkids_year2
replace nkids_year5=nkids_year5+1 if piq93e=="2"

*Kids at year (2002-2003)
gen nkids_year8=nkids_year5
replace nkids_year8=nkids_year8+1 if epi74e=="1"

*Number of kids per year
gen nkids_y1994=nkids_year0
gen nkids_y1995=nkids_year0
gen nkids_y1996=nkids_year2
gen nkids_y1997=nkids_year2
gen nkids_y1998=nkids_year2
gen nkids_y1999=nkids_year5
gen nkids_y2000=nkids_year5
gen nkids_y2001=nkids_year5
gen nkids_y2002=nkids_year8
gen nkids_y2003=nkids_year8


*Recovering local parameters of eitc by year-children
do "$codes/income/eitc.do"



forvalues y=1994/2003{
	
	*Subsidy amounts
	gen eitc_fed_y`y'=0
	gen eitc_state_y`y'=0
	
	
	replace eitc_fed_y`y'=r1_1_`y'*b1_1_`y' if (gross_y`y'>=b1_1_`y' & gross_y`y'<b2_1_`y') & nkids_y`y'==1
	replace eitc_fed_y`y'=r1_1_`y'*b1_1_`y'-r2_1_`y'*(gross_y`y'-b2_1_`y') if gross_y`y'>=b2_1_`y' & nkids_y`y'==1
	replace eitc_fed_y`y'=0 if eitc_fed_y`y'<0 & gross_y`y'>=b2_1_`y' & nkids_y`y'==1
	
	
	replace eitc_fed_y`y'=r1_2_`y'*b1_2_`y' if (gross_y`y'>=b1_2_`y' & gross_y`y'<b2_2_`y') & nkids_y`y'>=2
	replace eitc_fed_y`y'=r1_2_`y'*b1_2_`y'-r2_2_`y'*(gross_y`y'-b2_2_`y') if gross_y`y'>=b2_2_`y' & nkids_y`y'>=2
	replace eitc_fed_y`y'=0 if eitc_fed_y`y'<0 & gross_y`y'>=b2_2_`y' & nkids_y`y'>=2
	
	if `y'==1994{
		replace eitc_state_y`y'=min(state_1_1994*eitc_fed_y`y', min_state_1_1994 ) if nkids_y`y'==1
		replace eitc_state_y`y'=min(state_2_1994*eitc_fed_y`y', min_state_2_1994 ) if nkids_y`y'==2
		replace eitc_state_y`y'=min(state_3_1994*eitc_fed_y`y', min_state_3_1994 ) if nkids_y`y'==3
	}
	else{
		replace eitc_state_y`y'=state_1_`y'*eitc_fed_y`y' if nkids_y`y'==1
		replace eitc_state_y`y'=state_2_`y'*eitc_fed_y`y' if nkids_y`y'==2
		replace eitc_state_y`y'=state_3_`y'*eitc_fed_y`y' if nkids_y`y'>=3
	
	}
	
	*Total income
	egen total_income_y`y'=rowtotal(gross_y`y' eitc_fed_y`y' eitc_state_y`y')
	
	*For those who are in the treatment group
	if `y'<=2000{
		replace total_income_y`y'=total_income_y`y' + sup_y`y'
	}

}

sort sampleid
tempfile data_earn
save `data_earn',replace

******************************************
*FOOD STAMPS and AFDC BY QUARTERS SINCE RA
******************************************

*Use the CFS study
use "$databases/CFS_original.dta", clear
qui: do "$codes/data_cfs.do"


keep sampleid fsq* wwq* /*food stamps and afdc/WW payments*/

*Food stamps
qui destring fsq33 fsq34 fsq35 fsq36 fsq37, replace force

*AFDC and W-2 (wisconsin works)
qui destring wwq33 wwq34 wwq35 wwq36 wwq37, replace force 


*Assuming that q1-4 is year 1994 (need to do it to adjust for inflation)

local q1=1
forvalues y=1994/2003{
	local q2=`q1'+1
	local q3=`q2'+1
	local q4=`q3'+1
	egen afdc_y`y'=rowtotal(wwq`q1' wwq`q1' wwq`q1' wwq`q1')
	egen fs_y`y'=rowtotal(fsq`q1' fsq`q1' fsq`q1' fsq`q1')
	egen welfare_y`y'=rowtotal(afdc_y`y' fs_y`y')
	local q1=`q1'+4

}


*Merging with gross earnings+EITC
sort sampleid
merge 1:1 sampleid using `data_earn'
drop _merge

forvalues y=1994/2003{
	replace total_income_y`y'=total_income_y`y'+ welfare_y`y'

}

*Gross earnings v2: takes into account ww payments (assumed to be from 1997 onward)
forvalues y=1994/2003{
	
	if `y'<1997{
		gen grossv2_y`y'=gross_y`y'
		
	}
	else{
		gen grossv2_y`y'=gross_y`y' + afdc_y`y'
	}

}

*****************************************
*To real numbers (20003 dollars)
*****************************************


qui: do "$codes/income/cpi.do"

forvalues y=1994/2002{
	gen gross_nominal_y`y'=gross_y`y'
	replace total_income_y`y'=total_income_y`y'*cpi_`y'
	replace gross_y`y'=gross_y`y'*cpi_`y'
	replace grossv2_y`y'=grossv2_y`y'*cpi_`y'

}



*****************************************
*To years after RA
*****************************************
replace p_radatr=p_radatr+19000000
tostring p_radatr, force replace
gen ra_year=yofd(date(p_radatr,"YMD"))
format ra_year %ty
tab ra_year

keep total_income_y* gross_y* gross_nominal_y* grossv2_y* employment_y* sampleid ra_year afdc_y* fs_y* sup_y*
reshape long total_income_y gross_y gross_nominal_y grossv2_y employment_y afdc_y fs_y sup_y, i(sampleid) j(year)

*Years since RA
gen year_ra=year-ra_year


*Reshape again

*only one year behind
replace year_ra=year_ra+1 
keep year_ra total_income_y sampleid gross_y gross_nominal_y grossv2_y employment_y afdc_y fs_y sup_y
reshape wide total_income_y gross_y gross_nominal_y grossv2_y employment_y afdc_y fs_y sup_y, i(sampleid) j(year_ra)

*This database if for using it in the sample_model.do
sort sampleid
save "$results/Income/data_income.dta", replace
