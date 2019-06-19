#### a9

- shruti indicated work to start week of 6/17

#### digitalanalyst

- continue to make changes to the front end
    - meet w/andy to discuss some design approaches and involvement moving forward - done
    - flesh corners to the edge of screen   
        - look at the madw code for answers -NOT done
    - look into alternative coloring schemes -NOT done
    - rid of small orange strip -NOT done
    - make margins of the bubble window equivalent all the way around -NOT done

- continue to develop the ambig domain handler -NOT done
    - configure -NOT done
        - hope/wish/try -NOT done
- think through a possible date solution 
    - Approach
        - provided an input. 
            -> id date inputs
            -> id date usage - requesting value for a period, on spec'd date, etc.
            -> understand the existing schema and the storage of date entities
            -> reframe date inputs to fit the the desired schema usage
            -> tie date usage to function that will form sql query where statement to filter for given date conditions
    - continue to develop and test this approach. currently, there is a struggle in identifying date entities should they have adjoining characters. find a way to systemically be able to parse this information. currently, we have a regex implementation that could perform this. continue to work out this implementation in crossCheck. - not DONE


#### iwfm

- apply idea from email of implementations that speed up quadtree comps -done
- add in barcharts
    - continue to develop the barcharts
        - fix the xaxis. track down the translation function as being the possible culprit - done. no need for axes. range/height/y turned out to be the culprit
        - need to position properly together with other elements on the page. for some reason, the network vis wants to write to one of the two barcharts -DONE. BC there were multiple svgs on the page. specifying to write to svg doesn't exactly work. changed to d3.select('actualname)
        - another barrier conquered. the formatting of the container. essentially set each of the bar plot to the appropriate negative margin-top px to designate their positioning relative to one another and used transform: scale() to resize to something reasonable.
        - highlighting for mousover currently an issue. most likely a function of bad formatting. - NOT done
- tie barchart highlights to the tracking of time -NOT done
- add in coordinates to each bar chart to render opaque coordinates - NOT done
- provide appropriate nodes with the approriate coordinates - NOT done
    - we currently have the start period of each node in which we can use to deduce what the node is to put where - NOT done
    - set the initial coordinate of each node to their respective new hire/attrition bar where applicable - NOT done
    - cherry on the top? draining effect for each?

#### appchallenge

- get copy of azure -NOT done
- setup git -NOT done
- diagnose swim lanes, reframe approach -NOT done
- distribute info to team -NOT done
- wait on charge code -NOT done
- setup meeting to dicsuss approaches -NOT done