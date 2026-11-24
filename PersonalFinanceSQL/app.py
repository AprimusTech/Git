import sys, configparser, traceback
from pathlib import Path
from datetime import date
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit, QDateEdit, QGroupBox, QGridLayout)
from db import Database



TABLES = {
 'Transactions': {
  'table':'PF_Transactions','pk':'TransactionID','select':['TransactionID','TransactionDate','TransactionType','Category','Amount','AccountName','PaidBy','Description'],
  'columns':['ID','Date','Type','Category','Amount','Account','Paid By','Description'],
  'fields':[('TransactionDate','Date','date',False),('TransactionType','Type','combo',['Income','Expense']),('Category','Category','text'),('Amount','Amount','money'),('AccountName','Account','text'),('PaidBy','Paid By','text'),('Description','Description','multiline')],
  'order':'TransactionDate DESC, TransactionID DESC'},
 'Loans': {
  'table':'PF_Loans','pk':'LoanID','select':['LoanID','Lender','LoanType','LoanStartDate','OriginalAmount','OutstandingPrincipal','InterestRate','EMI','DueDay','TenureMonths','Notes'],
  'columns':['ID','Lender','Type','Start Date','Original','Outstanding','ROI %','EMI','Due Day','Tenure (mo)','Notes'],
  'fields':[('Lender','Bank / Lender','text'),('LoanType','Loan Type','combo',['Home Loan','Personal Loan','FlexiPay','Car Loan','Consumer Loan','Other']),('LoanStartDate','Start Date','date',True),('OriginalAmount','Original Amount','money'),('OutstandingPrincipal','Outstanding Principal','money'),('InterestRate','ROI % (annual)','money'),('EMI','Monthly EMI','money'),('DueDay','EMI Due Day','integer'),('TenureMonths','Tenure (months)','integer'),('Notes','Notes','multiline')], 'order':'Lender'},
 'Credit Cards': {
  'table':'PF_CreditCards','pk':'CardID','select':['CardID','CardName','Issuer','CreditLimit','Outstanding','StatementDay','DueDay','Notes'],
  'columns':['ID','Card','Issuer','Limit','Outstanding','Statement Day','Due Day','Notes'],
  'fields':[('CardName','Card Name','text'),('Issuer','Bank / Issuer','text'),('CreditLimit','Credit Limit','money'),('Outstanding','Outstanding','money'),('StatementDay','Statement Day','integer'),('DueDay','Payment Due Day','integer'),('Notes','Notes','multiline')], 'order':'CardName'},
 'Udhar': {
  'table':'PF_Udhar','pk':'UdharID','select':['UdharID','Direction','PersonName','TransactionDate','OriginalAmount','Outstanding','InterestRate','ExpectedDate','Notes'],
  'columns':['ID','Lent / Borrowed','Person','Date','Original','Balance','ROI %','Expected Date','Notes'],
  'fields':[('Direction','Direction','combo',['Lent (Receivable)','Borrowed (Payable)']),('PersonName','Person Name','text'),('TransactionDate','Date','date',False),('OriginalAmount','Original Amount','money'),('Outstanding','Outstanding Balance','money'),('InterestRate','ROI % (annual)','money'),('ExpectedDate','Expected Repayment','date',True),('Notes','Notes','multiline')], 'order':'TransactionDate DESC, UdharID DESC'},
 'Accounts': {
  'table':'PF_Accounts','pk':'AccountID','select':['AccountID','AccountName','AccountType','OpeningBalance','Notes','IsActive'],
  'columns':['ID','Account','Type','Opening Balance','Notes','Active'],
  'fields':[('AccountName','Account Name','text'),('AccountType','Type','combo',['Bank','Cash','Wallet','Investment','Other']),('OpeningBalance','Opening Balance','money'),('Notes','Notes','multiline'),('IsActive','Active','combo',['Yes','No'])], 'order':'AccountName'}
}

class RecordDialog(QDialog):
    def __init__(self, parent, fields, record=None):
        super().__init__(parent); self.fields=fields; self.widgets={}; self.record=record or {}
        self.setWindowTitle('Edit record' if record else 'Add record'); self.resize(440,500)
        form=QFormLayout();
        for field in fields:
            key,label,kind,*extras=field; optional=bool(extras[0]) if kind=='date' and extras else False
            if kind=='text': w=QLineEdit()
            elif kind=='money':
                w=QDoubleSpinBox(); w.setRange(-999999999,999999999); w.setDecimals(2); w.setSingleStep(100)
            elif kind=='integer': w=QSpinBox(); w.setRange(0,1000000)
            elif kind=='combo':
                w=QComboBox(); w.addItems(extras[0]);
                if key=='IsActive': w.setCurrentText('Yes')
            elif kind=='multiline': w=QTextEdit(); w.setMaximumHeight(90)
            elif kind=='date':
                w=QDateEdit(); w.setCalendarPopup(True); w.setDisplayFormat('dd-MMM-yyyy'); w.setDate(QDate.currentDate())
                if optional:
                    chk=QComboBox(); chk.addItems(['No date','Set date']); self.widgets[key+'_enabled']=chk
                    row=QHBoxLayout(); row.addWidget(chk); row.addWidget(w); holder=QWidget(); holder.setLayout(row); form.addRow(label,holder)
                else: form.addRow(label,w)
            if kind!='date': form.addRow(label,w)
            self.widgets[key]=w
        if record:
            for key,_,kind,*extras in fields:
                val=record.get(key)
                if val is None: continue
                w=self.widgets[key]
                if kind=='date':
                    if extras and extras[0]: self.widgets[key+'_enabled'].setCurrentText('Set date')
                    w.setDate(QDate(val.year,val.month,val.day))
                elif kind=='text': w.setText(str(val))
                elif kind=='money': w.setValue(float(val))
                elif kind=='integer': w.setValue(int(val))
                elif kind=='combo': w.setCurrentText('Yes' if key=='IsActive' and val else 'No' if key=='IsActive' else str(val))
                elif kind=='multiline': w.setPlainText(str(val))
        buttons=QHBoxLayout(); save=QPushButton('Save'); cancel=QPushButton('Cancel'); save.clicked.connect(self.accept); cancel.clicked.connect(self.reject); buttons.addWidget(save); buttons.addWidget(cancel)
        layout=QVBoxLayout(self); layout.addLayout(form); layout.addLayout(buttons)
    def values(self):
        result={}
        for key,label,kind,*extras in self.fields:
            w=self.widgets[key]
            if kind=='text': v=w.text().strip()
            elif kind=='money': v=w.value()
            elif kind=='integer': v=w.value(); v=None if v==0 else v
            elif kind=='combo': v=w.currentText(); v=(1 if v=='Yes' else 0) if key=='IsActive' else v
            elif kind=='multiline': v=w.toPlainText().strip() or None
            elif kind=='date':
                optional=bool(extras and extras[0]); v=w.date().toPython()
                if optional and self.widgets[key+'_enabled'].currentText()=='No date': v=None
            result[key]=v
        return result


class CrudTab(QWidget):
    def __init__(self, db, config):
        super().__init__(); self.db=db; self.config=config; self.table=QTableWidget(); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection); self.table.horizontalHeader().setStretchLastSection(True)
        buttons=QHBoxLayout();
        for text,fn in [('Add',self.add),('Edit Selected',self.edit),('Delete Selected',self.delete),('Refresh',self.refresh)]:
            b=QPushButton(text); b.clicked.connect(fn); buttons.addWidget(b)
        layout=QVBoxLayout(self); layout.addLayout(buttons); layout.addWidget(self.table); self.refresh()
    def refresh(self):
        c=self.config
        self.table.setColumnCount(len(c['columns'])); self.table.setHorizontalHeaderLabels(c['columns']); self.table.setRowCount(0)
        if not self.db.connection_string: return
        try:
            with self.db.connect() as conn:
                cur=conn.cursor(); sql='SELECT '+','.join(c['select'])+' FROM dbo.'+c['table']+' ORDER BY '+c['order']; cur.execute(sql); rows=cur.fetchall()
            self.table.setColumnCount(len(c['columns'])); self.table.setHorizontalHeaderLabels(c['columns']); self.table.setRowCount(len(rows))
            for r,row in enumerate(rows):
                for col,val in enumerate(row):
                    if c['table']=='PF_Accounts' and col==5: val='Yes' if val else 'No'
                    if isinstance(val,float): val=f'{val:,.2f}'
                    item=QTableWidgetItem('' if val is None else str(val)); item.setData(Qt.ItemDataRole.UserRole,row[0]); self.table.setItem(r,col,item)
            self.table.resizeColumnsToContents()
        except Exception as e: QMessageBox.critical(self,'SQL Server Error',str(e))
    def selected_record(self):
        row=self.table.currentRow()
        if row<0: return None
        rid=self.table.item(row,0).data(Qt.ItemDataRole.UserRole)
        c=self.config
        with self.db.connect() as conn:
            cur=conn.cursor(); cur.execute('SELECT '+','.join(c['select'])+' FROM dbo.'+c['table']+' WHERE '+c['pk']+'=?',rid); data=cur.fetchone()
        return dict(zip(c['select'],data)) if data else None
    def add(self):
        dlg=RecordDialog(self,self.config['fields']);
        if dlg.exec(): self.save_record(dlg.values(),None)
    def edit(self):
        rec=self.selected_record()
        if not rec: QMessageBox.information(self,'Select record','Please select a row first.'); return
        dlg=RecordDialog(self,self.config['fields'],rec)
        if dlg.exec(): self.save_record(dlg.values(),rec[self.config['pk']])
    def save_record(self,vals,rid):
        c=self.config; keys=list(vals); placeholders=','.join('?' for _ in keys)
        try:
            with self.db.connect() as conn:
                cur=conn.cursor()
                if rid is None:
                    cur.execute('INSERT INTO dbo.'+c['table']+' ('+','.join(keys)+') VALUES ('+placeholders+')',tuple(vals[k] for k in keys))
                else:
                    assignments=','.join(k+'=?' for k in keys); cur.execute('UPDATE dbo.'+c['table']+' SET '+assignments+' WHERE '+c['pk']+'=?',tuple(vals[k] for k in keys)+(rid,))
                conn.commit()
            self.refresh()
        except Exception as e: QMessageBox.critical(self,'Save failed',str(e))
    def delete(self):
        rec=self.selected_record()
        if not rec: QMessageBox.information(self,'Select record','Please select a row first.'); return
        if QMessageBox.question(self,'Confirm delete','Delete the selected record?')!=QMessageBox.StandardButton.Yes: return
        c=self.config
        try:
            with self.db.connect() as conn: conn.cursor().execute('DELETE FROM dbo.'+c['table']+' WHERE '+c['pk']+'=?',rec[c['pk']]); conn.commit()
            self.refresh()
        except Exception as e: QMessageBox.critical(self,'Delete failed',str(e))

class Dashboard(QWidget):
    def __init__(self,db):
        super().__init__(); self.db=db; self.cards={}; grid=QGridLayout(self)
        names=['Income This Month','Expenses This Month','Loan Outstanding','Credit Card Outstanding','Money Lent','Money Borrowed','Net Cash Flow']
        for i,n in enumerate(names):
            box=QGroupBox(n); v=QVBoxLayout(box); lab=QLabel('₹ —'); lab.setStyleSheet('font-size:22px;font-weight:700;color:#187a60'); v.addWidget(lab); grid.addWidget(box,i//3,i%3); self.cards[n]=lab
        refresh=QPushButton('Refresh Dashboard'); grid.addWidget(refresh,3,0); refresh.clicked.connect(self.refresh); self.refresh()
    def refresh(self):
        try:
            with self.db.connect() as conn:
                cur=conn.cursor()
                cur.execute("SELECT COALESCE(SUM(CASE WHEN TransactionType='Income' THEN Amount END),0), COALESCE(SUM(CASE WHEN TransactionType='Expense' THEN Amount END),0) FROM dbo.PF_Transactions WHERE YEAR(TransactionDate)=YEAR(GETDATE()) AND MONTH(TransactionDate)=MONTH(GETDATE())"); income,expense=cur.fetchone()
                cur.execute('SELECT COALESCE(SUM(OutstandingPrincipal),0) FROM dbo.PF_Loans'); loans=cur.fetchone()[0]
                cur.execute('SELECT COALESCE(SUM(Outstanding),0) FROM dbo.PF_CreditCards'); cards=cur.fetchone()[0]
                cur.execute("SELECT COALESCE(SUM(CASE WHEN Direction LIKE 'Lent%' THEN Outstanding END),0),COALESCE(SUM(CASE WHEN Direction LIKE 'Borrowed%' THEN Outstanding END),0) FROM dbo.PF_Udhar"); lent,borrowed=cur.fetchone()
            vals={'Income This Month':income,'Expenses This Month':expense,'Loan Outstanding':loans,'Credit Card Outstanding':cards,'Money Lent':lent,'Money Borrowed':borrow,'Net Cash Flow':income-expense}
            for k,v in vals.items(): self.cards[k].setText('₹ {:,.2f}'.format(float(v or 0)))
        except Exception as e:
            self.cards['Income This Month'].setText('Connect SQL Server to view dashboard')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.db=Database(); self.setWindowTitle('Personal Finance Manager | SQL Server Edition'); self.resize(1280,800)
        self.setStyleSheet('QMainWindow{background:#f4f6f8;} QTabWidget::pane{border:1px solid #d7dce2;background:white;} QPushButton{padding:7px 12px;} QGroupBox{font-weight:600;background:white;border:1px solid #d7dce2;border-radius:8px;margin-top:8px;padding:8px;} QTableWidget{background:white;alternate-background-color:#f6f8fa;}')
        self.ensure_schema()
        tabs=QTabWidget(); tabs.addTab(Dashboard(self.db),'Dashboard')
        for name,config in TABLES.items(): tabs.addTab(CrudTab(self.db,config),name)
        self.setCentralWidget(tabs); self.create_menu()
    def create_menu(self):
        menu=self.menuBar().addMenu('Database'); act=menu.addAction('Configure SQL Server…'); act.triggered.connect(self.configure); init=menu.addAction('Initialize / Verify Tables'); init.triggered.connect(self.ensure_schema)
        helpmenu=self.menuBar().addMenu('Help'); info=helpmenu.addAction('About'); info.triggered.connect(lambda: QMessageBox.information(self,'About','Personal Finance Manager\nPython + PySide6 + Microsoft SQL Server\nLocal-first desktop application.'))
    def configure(self):
        cfg=configparser.ConfigParser(); cfg.read(self.db.config_path) if self.db.config_path.exists() else None
        current=cfg.get('sqlserver','connection_string',fallback='') if cfg.has_section('sqlserver') else ''
        dlg=QDialog(self); dlg.setWindowTitle('SQL Server Connection'); dlg.resize(650,220); layout=QVBoxLayout(dlg)
        layout.addWidget(QLabel('ODBC connection string (example: SQL Server Express using Windows authentication):'))
        edit=QTextEdit(); edit.setPlainText(current); layout.addWidget(edit)
        buttons=QHBoxLayout(); test=QPushButton('Test Connection'); save=QPushButton('Save'); close=QPushButton('Cancel'); buttons.addWidget(test); buttons.addWidget(save); buttons.addWidget(close); layout.addLayout(buttons)
        def test_conn():
            try: pyconn=__import__('pyodbc').connect(edit.toPlainText().strip(),timeout=5); pyconn.close(); QMessageBox.information(dlg,'Success','SQL Server connection succeeded.')
            except Exception as e: QMessageBox.critical(dlg,'Connection failed',str(e))
        test.clicked.connect(test_conn)
        def save_conn():
            cfg['sqlserver']={'connection_string':edit.toPlainText().strip()};
            with open(self.db.config_path,'w') as f: cfg.write(f)
            self.db.connection_string=edit.toPlainText().strip(); QMessageBox.information(dlg,'Saved','Connection settings saved.'); dlg.accept(); self.ensure_schema()
        save.clicked.connect(save_conn); close.clicked.connect(dlg.reject); dlg.exec()
    def ensure_schema(self):
        try:
            schema=Path(__file__).with_name('schema.sql').read_text(encoding='utf-8')
            statements=[s.strip() for s in schema.split(';') if s.strip()]
            with self.db.connect() as conn:
                cur=conn.cursor()
                for statement in statements:
                    # Make the starter schema safe to run repeatedly.
                    table_name=statement.split('CREATE TABLE dbo.',1)[1].split(' ',1)[0]
                    cur.execute("IF OBJECT_ID('dbo."+table_name+"','U') IS NULL BEGIN "+statement+" END")
                conn.commit()
        except Exception as e:
            # Startup remains available so connection can be configured from the menu.
            print('SQL initialization:',e)

def main():
    app=QApplication(sys.argv); win=MainWindow(); win.show(); sys.exit(app.exec())
if __name__=='__main__': main()
