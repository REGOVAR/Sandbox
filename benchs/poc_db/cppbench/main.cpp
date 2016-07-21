#include "Variant.h"
#include <chrono>
#include <thread> 
#include <mutex> 
#include <pqxx/pqxx> 

using namespace std;
using namespace chrono;
using namespace vcflib;
using namespace pqxx;


mutex m;
int jobInProgress = 0;



void normalize(long& pos, string& ref, string& alt)
{
    if (ref == alt)
    {
        // not a variant -> cancel it
        ref = ".";
        alt = ".";
    }

    while (ref.length() > 0 && alt.length() && ref.at(0) == alt.at(0))
    {
      ref = ref.substr(1);
      alt = alt.substr(1);
      ++pos;
    }

    if (ref.length() == alt.length())
    {
        while (ref.length() > 0 && alt.length() && ref.at(0) == alt.at(0))
        {
            ref = ref.substr(0, ref.length()-1);
            alt = alt.substr(0, alt.length()-1);
        }
    }
}


void asynchSqlExec(string sqlQuery)
{
    m.lock();
    jobInProgress += 1;
    m.unlock();




    try
    {
        connection C("dbname=regovar-dev user=regovar password=regovar hostaddr=127.0.0.1 port=5433");
        if (C.is_open()) 
        {
            cout << "Opened database successfully: " << C.dbname() << endl;
        } 
        else 
        {
            cout << "Can't open database" << endl;
            m.lock();
            jobInProgress -=1;
            m.unlock();
        }


        cout << " Start exec asynch " << jobInProgress << endl;
        nontransaction N(C);
        N.exec( sqlQuery );

        C.disconnect ();
    }
    catch (const exception &e)
    {

        cerr << e.what() << endl;

        m.lock();
        jobInProgress -=1;
        m.unlock();

        return;
    }


    m.lock();
    jobInProgress -=1;
    m.unlock();
}









int main(int argc, char** argv)
{
    //return 0;


    time_point<system_clock> start, end;


    start = system_clock::now();
    VariantCallFile variantFile;

    if (argc > 1) 
    {
        string filename = argv[1];
        variantFile.open(filename);
    } 
    else 
    {
        variantFile.open(std::cin);
    }

    if (!variantFile.is_open()) 
    {
        return 1;
    }

    Variant var(variantFile);
    string sqlQuery = "";
    string sqlHead  = "INSERT INTO _2_variant (sample_id, chr, pos, ref, alt, is_transition) VALUES ";
    string sqlTail  = " ON CONFLICT DO NOTHING";
    long count = 0;
    while (variantFile.getNextVariant(var)) 
    {
        //cout << "===== " << var.sequenceName << ", " << var.position << endl;

        /*
        for (auto& it : var.flatAlternates())
        {
            cout << "   >" << it.first   << " : ";
            for (auto& it2 : it.second) 
            {
                cout << "(" << var.sequenceName << ", " << it2.position << ", " << it2.ref << ", " << it2.alt << ") ";
            }
        }
        cout << endl;*/

        // first we normalize all alleles for this vcf entry
        vector<string> alts = var.alleles;
        vector<long> poss;
        vector<string> refs;
        for (uint i=0; i<alts.size(); i++)
        {
            poss.push_back(var.position);
            refs.push_back(var.ref);

            normalize(poss[i], refs[i], alts[i]);
        }

        // Then for each sample we register only "true" variant
        for (auto& it : var.samples) 
        {

            //cout << "  sample " << it.first << " (" << it.second["GT"][0] << ") : " ;
            vector<string> genotype;
            if (it.second["GT"][0].find('/') != std::string::npos)
            {
                genotype = split(it.second["GT"][0], '/');
            }
            else
            {
                genotype = split(it.second["GT"][0], '|');
            }


            if (genotype[0] != "."  && genotype[0] != "0")
            {
                int idx = stoi(genotype[0]);
                sqlQuery += "(" + to_string(1) + ",'" + var.sequenceName + "'," + to_string(poss[idx]) + ",'" + refs[idx] + "','" + alts[idx] + "', TRUE ),";
                ++count;
                //cout << "[" << poss[idx] << ", " <<  refs[idx] << ", " << alts[idx] << "] ";
            }
            if (genotype[1] != "." && genotype[1] != "0")
            {
                int idx = stoi(genotype[1]);
                sqlQuery += "(" + to_string(1) + ",'" + var.sequenceName + "'," + to_string(poss[idx]) + ",'" + refs[idx] + "','" + alts[idx] + "', TRUE ),";
                ++count;
                //cout << "[" << poss[idx] << ", " <<  refs[idx] << ", " << alts[idx] << "] ";
            }

            if (count > 1000000)
            {
                thread execReq(asynchSqlExec, sqlHead + sqlQuery.substr(0, sqlQuery.length()-1) + sqlTail); 
                execReq.join();
                sqlQuery = "";
                count = 0;
            }
        }
    } // end vcf parsing loop

    end = system_clock::now();
    duration<double> elapsed_seconds = end-start;
    cout << "parsing done in " << elapsed_seconds.count() << " s" << endl;


    thread execReq(asynchSqlExec, sqlHead + sqlQuery.substr(0, sqlQuery.length()-1) + sqlTail); 
    execReq.join();
    int current = 0;
    while (jobInProgress > 0)
    {
        if (current != jobInProgress)
        {
          cout << "remaining sql job : " << jobInProgress;
          current = jobInProgress;
        }
    }

    end = system_clock::now();
    elapsed_seconds = end-start;
    cout << "import done in " << elapsed_seconds.count() << " s" << endl;

    return 0;
}