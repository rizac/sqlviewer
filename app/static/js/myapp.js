angular.module('myApp', [])
.controller('myCtrl', function ($scope, $http, $window) {
    $scope.dbAddress = "";
    $scope.schemas = {}; // $scope.schemas = {schema [string]: tables [Object]},
    //where tables is in turn an object of pairs: {name [string]: rows [int]}
    $scope.tables = {}; // It is $scope.schemas[$scope.selectedSchemaName] || {}
    $scope.selectedSchemaName = "";
    $scope.selectedTable = undefined;
    $scope.errorMsg = null;
    $scope.working=false;
    $scope.showWindowPopup = false;
    $scope.windowPopupRawContent = "";
    $scope.DEFAULT_NUM_ROWS = 20;
    $scope.MAX_CELL_STR_LEN = 2000;
    // not used for now but leave them here:
    $scope._numericTypesStarts=["INTEGER", "SMALLINT", "INTEGER", "BIGINT", "DECIMAL",
                                  "NUMERIC", "FLOAT", "REAL", "FLOAT", "DOUBLE PRECISION"];
    $scope._textTypesStarts = ["CHARACTER", "VARCHAR", "CHARACTER VARYING"];
    
    $scope.len = function(obj){
    	return obj ? (obj.length !== undefined ? obj.length :  Object.keys(obj).length) : 0;
    }
    
    $scope.showInPopup = function(rawStr){
    	$scope.windowPopupRawContent = rawStr;
    	$scope.showWindowPopup = 'rawContent';
    }
    
    $window.onbeforeunload = function(){
    	//send a request to close the app:
    	$http.post("/close", JSON.stringify({}),
        		{headers: {'Content-Type': 'application/json'}});
        return null;
    }
    
    $scope.queryDb = function() {
    	$scope.setWorking(true);
    	$scope.schemas = {};
    	$scope.setSelectedSchemaName("");
    	var data = {
        	url: $scope.dbAddress
        };
        $http.post("/query_db", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}
        ).then(function(response) {
        	data = response.data;
        	var schemas = data.schemas;
        	for(var j=0; j<schemas.length; j++){
        		var schemaName = schemas[j][0];
        		var tablesAndInst = schemas[j][1];
        		var tables = {};
        		for(var i=0; i<tablesAndInst.length; i++){
        			tables[tablesAndInst[i][0]] = tablesAndInst[i][1];
        		}
        		$scope.schemas[schemaName] = tables;
        	}
            if(schemas.length==1){
            	$scope.setSelectedSchemaName(schemas[0][0]);
            }
            $scope.setWorking(false);
        }, function(response) {
            $scope.setWorking(false);
            // error handler. Must come after setWorking
        	$scope.handleError(response);
        });
    }

    $scope.setSelectedSchemaName = function(schema){
    	$scope.selectedSchemaName = schema;
    	$scope.tables = $scope.schemas[schema] || {};
    	$scope.setSelectedTableName("");
    	if ($scope.len($scope.tables)==1){
    		for (tableName in $scope.tables) break;
    		$scope.setSelectedTableName(tableName);
    	}
    }
    $scope.setSelectedTableName = function(tableName){
    	$scope.selectedTable = undefined;
    	$scope.queryTable(tableName);
    }
    $scope.queryTable = function(tableName) {
    	if (!tableName){return;}
    	$scope.setWorking(true);
    	var startRow = $scope.selectedTable ? $scope.selectedTable.view[1] : 0;
        var data = {
        	schema_name: $scope.selectedSchemaName,
            table_name: tableName,
        	start_row: startRow,
        	num_results: $scope.selectedTable ? $scope.selectedTable.view[2] - $scope.selectedTable.view[1] : $scope.DEFAULT_NUM_ROWS,
        	order_colname: $scope.selectedTable ? $scope.selectedTable.orderColName : null,
        	order_ascending: $scope.selectedTable ? $scope.selectedTable.orderAscending : true
        };
        $http.post("/query_table", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}
        ).then(function(response) { // success handler
        	var data = response.data;
        	if (!$scope.selectedTable){
        		$scope.selectedTable = {};
        	}
        	var st = $scope.selectedTable;
        	st.name = tableName;
        	st.view = [0, startRow, startRow + data.data.length, $scope.schemas[$scope.selectedSchemaName][tableName]];
        	st.data = data.data;
        	st.columns = data.columns;
        	st.types = data.types;
        	st.pyTypes = data.python_types;
        	st.foreignKeys = data.fk || [];
        	st.primaryKey = data.pk || {};
        	st.uniqueConstraints = data.uc || [];
        	st.checkConstraints = data.cc || [];
        	st.indexes = data.idx || [];
        	st.sqlCreateText = data.sql_create || "";
        	$scope.setWorking(false);
        }, function(response) {
        	$scope.setWorking(false);
        	// error handler. Must come after setWorking
        	$scope.handleError(response);
        });
    }
    $scope.toggleColSort = function(colname){
    	var selT = $scope.selectedTable;
    	if (!selT){
    		return;
    	}
    	if (colname != selT.orderColName){
    		selT.orderAscending = true;  // will be set to true below
    	}else{
    		selT.orderAscending = !selT.orderAscending;
    	}
    	selT.orderColName = colname;
    	$scope.queryTable(selT.name);
    }
    $scope.changeView = function(direction){
    	var selT = $scope.selectedTable;
    	if (!selT){
    		return;
    	}
    	var DEF_NUM_ROWS = $scope.DEFAULT_NUM_ROWS;
    	if(direction == 'end'){
    		var mod = selT.view[3] % DEF_NUM_ROWS;
    		selT.view[1] = mod == 0 ? selT.view[3] - DEF_NUM_ROWS : selT.view[3] - mod;
    	}else if(direction == 'start'){
    		selT.view[1] = 0;
    	}else if(direction > 0){
	    	selT.view[1] += DEF_NUM_ROWS;
	    }else if(direction < 0){
	    	selT.view[1] -= DEF_NUM_ROWS;
	    }else{
	    	return;
	    }
    	selT.view[2] = selT.view[1] + DEF_NUM_ROWS;
    	$scope.queryTable(selT.name);
    }
    $scope.setWorking = function(value){
    	$scope.clearErrorMsg();
    	$scope.working = value;
    };
    $scope.clearErrorMsg = function(){
    	$scope.errorMsg = null;
    }
    $scope.handleError = function(error){
    	$scope.errorMsg = "";
    	if (!error){
    		return;
    	}
    	if (error.status){
    		$scope.errorMsg = "[" + error.status + "] ";
    	}
    	if (error.data){
    		$scope.errorMsg += (error.data.message || error.data) + "";
    	}else{
    		$scope.errorMsg += error + "";
    	}
    }
    // see http://docs.sqlalchemy.org/en/latest/core/reflection.html
    $scope.getForeignKeyIndex = function(colName){
    	var fks = $scope.selectedTable ? $scope.selectedTable.foreignKeys : [];
    	for (var i=0; i<fks.length; i++){
    		if (fks[i].constrained_columns.indexOf(colName)>-1){
    			return i;
    		}
    	}
    	return -1;
    }
    $scope.isPrimaryKey = function(colName){
    	var pk = $scope.selectedTable ? $scope.selectedTable.primaryKey : {};
    	return pk.constrained_columns ? pk.constrained_columns.indexOf(colName) > -1 : false;
    }
    $scope.getUniqueConstraintsIndex = function(colName){
    	var ucs = $scope.selectedTable ? $scope.selectedTable.uniqueConstraints : [];
    	for (var i=0; i<ucs.length; i++){
    		if (ucs[i].column_names.indexOf(colName)>-1){
    			return i;
    		}
    	}
    	return -1;
    }
    $scope.getIndexesIndex = function(colName){
    	var idxs = $scope.selectedTable ? $scope.selectedTable.indexes : [];
    	for (var i=0; i<idxs.length; i++){
    		if (idxs[i].column_names.indexOf(colName)>-1){
    			return i;
    		}
    	}
    	return -1;
    }
    
    $scope.queryCmdlineAddress = function() {
        $http.post("/query_cmdline_address", {},
        		{headers: {'Content-Type': 'application/json'}}
        ).then(function(response) {
        	data = response.data || {};
        	$scope.dbAddress = data.dburl || "";
        	if ($scope.dbAddress){
        		$scope.queryDb(); 
        	}
        }, function(response) {
            //$scope.setWorking(false);
            // error handler. Must come after setWorking
        	//$scope.handleError(response);
        });
    }
    // see if we passed the db url in the command line
    $scope.queryCmdlineAddress();
     
})

