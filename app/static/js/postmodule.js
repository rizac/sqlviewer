angular.module('myApp', [])
.controller('myCtrl', function ($scope, $http) {
    $scope.dbAddress = "";
    $scope.schemas = {}; // $scope.schemas = {schema [string]: tables [Object]},
    //where tables is in turn an object of pairs: {name [string]: rows [int]}
    $scope.tables = {}; // It is $scope.schemas[$scope.selectedSchemaName] || {}
    $scope.selectedSchemaName = "";
    $scope.selectedTable = undefined;
    $scope.errorMsg = null;
    $scope.working=false;
    $scope.showSelTableDetails = false;
    $scope._numericTypesStarts=["INTEGER", "SMALLINT", "INTEGER", "BIGINT", "DECIMAL",
                                  "NUMERIC", "FLOAT", "REAL", "FLOAT", "DOUBLE PRECISION"];
    $scope._textTypesStarts = ["CHARACTER", "VARCHAR", "CHARACTER VARYING"];
    $scope.showDetails = function(val){
    	if(!val || !$scope.selectedTable){
    		$scope.selTableDetails = "";
    	}else{
    		var st = $scope.selectedTable;
    		$scope.selTableDetails = "primary key constraint (pk)\n" + JSON.stringify(st.primaryKey) +
    			"Foreign keys (fk)\n" + JSON.stringify(st.foreignKeys) + "\n" +
    			"Unique constraints (uc)\n" + JSON.stringify(st.uniqueConstraints) +
    			"Indexes (idx)\n" + JSON.stringify(st.indexes);
    	}
    }
    
    $scope.len = function(obj){
    	return obj ? (obj.length !== undefined ? obj.length :  Object.keys(obj).length) : 0;
    }

    $scope.queryDb = function() {
    	$scope.working=true;
    	$scope.schemas = {};
    	$scope.setSelectedSchemaName("");
    	var data = {
        	url: $scope.dbAddress
        };
        $http.post("/query_db", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}
        ).then(function(response) {
        	data = response.data;
        	//url might be different than the supplied one if we are init (see set_cache_address
        	// in core.sql)
        	$scope.dbAddress = data.dburl;
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
            $scope.working=false;
        }, function(response) {
            // error handler
        	$scope.handleError(response);
        	$scope.working=false;
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
    	if (!tableName){
    		return;
    	}
    	$scope.working=true;
        var data = {
        	schema_name: $scope.selectedSchemaName,
            table_name: tableName,
        	start_row: 0,
        	num_results: 20,
        	order_colname: $scope.selectedTable ? $scope.selectedTable.orderColName : null,
        	order_ascending: $scope.selectedTable ? $scope.selectedTable.orderAscending : true
        };
        $http.post("/query_table", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}
        ).then(function(response) { // success handler
        	data = response.data;
        	if (!$scope.selectedTable){
        		$scope.selectedTable = {};
        	}
        	var st = $scope.selectedTable;
        	st.name = tableName;
        	st.data = data.data;
        	st.columns = data.columns;
        	st.types = data.types;
        	st.foreignKeys = data.fk || [];
        	st.primaryKey = data.pk || {};
        	st.uniqueConstraints = data.uc || [];
        	st.indexes = data.idx || [];
        	/* create boolean of whether each col is numeric or text (used e.g. for css align) */
        	st.typeIsNumeric = [];
        	st.typeIsText = [];
        	var nts = $scope._numericTypesStarts;
        	var tts = $scope._textTypesStarts
        	for (var i=0; i< st.types.length; i++){
        		var _type = st.types[i]; //.trim().toUpperCase();
        		for (var j=0; j< nts.length; j++){
        			if (_type.startsWith(nts[j])){
        				st.typeIsNumeric.push(true);
        				st.typeIsText.push(false);
        				break;
        			}
        		}
        		if(st.typeIsNumeric.length == i){ // was not numeric
        			for (var j=0; j< tts.length; j++){
            			if (_type.startsWith(tts[j])){
            				st.typeIsNumeric.push(false);
            				st.typeIsText.push(true);
            				break;
            				}
            			}
        		}
        		if(st.typeIsNumeric.length == i){ // was not numeric, nor text
        			st.typeIsNumeric.push(false);
    				st.typeIsText.push(false);
        		}
        	}
        	$scope.working=false;
        }, function(response) {  // error handler
        	$scope.handleError(response);
        	$scope.working=false;
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
    $scope.queryDb();  // see if we passed the db url in the command line
})

