import coral
import nameDealer
class idDealer(object):
    """Manages the autoincremental ID values.\n
    Input: coral.schema object
    """
    def __init__( self , schema  ):
        self.__schema = schema
        self.__idTableColumnName = 'NEXTID'
        self.__idTableColumnType = 'unsigned long long'
        
    def getIDColumnDefinition( self ):
        return (self.__idTableColumnName, self.__idTableColumnType)
    
    def getIDforTable( self, tableName ):
        """
        get the new id value to use for the given table
        """
        try:
            idtableName = nameDealer.idTableName(tableName)
            query = self.__schema.tableHandle(idtableName).newQuery()
            query.addToOutputList(self.__idTableColumnName)
            query.setForUpdate() #lock it
            cursor = query.execute()
            result = 0
            while ( cursor.next() ):
                result = cursor.currentRow()[self.__idTableColumnName].data()
            del query
            return result
        except Exception, e:
            raise Exception, str(e)

    def generateNextIDForTable( self, tableName ):
        """
        Set the nextID in the IDTableName to current id value + 1 .\n
        Input: ID table name.
        """
        try:
            idtableName = nameDealer.idTableName(tableName)
            tableHandle = self.__schema.tableHandle(idtableName)
            query = tableHandle.newQuery()
            query.addToOutputList(self.__idTableColumnName)
            query.setForUpdate() #lock it
            cursor = query.execute()
            result = 0
            while ( cursor.next() ):
                result = cursor.currentRow()[0].data()
            del query            
            dataEditor = tableHandle.dataEditor()
            inputData = coral.AttributeList()
            if result==0: #is a new table, no entry in the id table
                dataEditor.rowBuffer(inputData)
                inputData[self.__idTableColumnName].setData(result+1)
                dataEditor.insertRow(inputData) 
            else:                
                inputData.extend( 'newid', self.__idTableColumnType )
                inputData['newid'].setData(result+1)
                dataEditor.updateRows('NEXTID = :newid','',inputData)
            return result+1
        except Exception, e:
            raise Exception, str(e)

if __name__ == "__main__":
    fakeIDtableName='Fake_ID'
    svc=coral.ConnectionService()
    session=svc.connect('sqlite_file:fake.db')
    transaction=session.transaction()
    try:
        transaction.start(False)
        schema=session.nominalSchema()
        idor=idDealer(schema)
        if schema.existsTable(fakeIDtableName) is False:
          description=coral.TableDescription()
          description.setName(fakeIDtableName)
          description.setPrimaryKey(idor.getIDColumnDefinition()[0])        
          description.insertColumn(idor.getIDColumnDefinition()[0],idor.getIDColumnDefinition()[1])
          idtableHandle=schema.createTable(description)
          idtableHandle.privilegeManager().grantToPublic(coral.privilege_Select)
        idor.generateNextIDForTable('Fake')
        print idor.getIDforTable('Fake')
        transaction.commit()
        del session
    except coral.Exception,e:
        transaction.rollback()
        del session
    except Exception, e:
        print 'failed in unit test'
        print str(e)
        del session