clear all
clc
close all
%addpath('C:\Users\Julio Valenzuela\Dropbox\matlab_physics')
%addpath('F:\Unidades compartidas\llampudken_data\osc_data')
currentFolderA = pwd;
%% selecciona el disparo, "shot", que se desea abrir
Ndisparo=1558;


%List3054=dir(['shot' num2str(Ndisparo) '_*_' 'tds3054.txt'])
%name3054=List3054.name

List = dir(['shot' num2str(Ndisparo) '*.txt']');
nameshot=List.name;
fechaindex=strfind(nameshot,'_');
fecha=nameshot(fechaindex(1)+1:fechaindex(2)-1)%

shot=['shot' num2str(Ndisparo) '_' fecha]%
%% factores de calibracion rogowski
fR1=1.40*1e9*10; %A/(Vs), incluye atenuacion de 20dB
fR2=1.96*1e9*10; %A/(Vs), incluye atenuacion de 20dB
fR3=1.90*1e9*100; %A/(Vs) incluye atenuacion de 20dB x2
fPr=1400*2; %kA/V, el factor 2 es del divisor de potencia antes del integrador, nueva calibración hecha el 25 ctubre 2021, disparos 359, 360, 361
%% abre archivo osc_channels que contine informacion de los canales en los osciloscopios

if Ndisparo>=229 && Ndisparo < 249
    fid=fopen('osc_channels_229.txt');

    elseif Ndisparo>=249 && Ndisparo < 310
    fid=fopen('osc_channels_249.txt');

    elseif Ndisparo>=310 && Ndisparo < 357
    fid=fopen('osc_channels_310.txt');

    elseif Ndisparo>=357 && Ndisparo < 365
    fid=fopen('osc_channels_357.txt');

    elseif Ndisparo>=365 && Ndisparo < 372
    fid=fopen('osc_channels_365.txt');

    elseif Ndisparo>=372 && Ndisparo < 398
    fid=fopen('osc_channels_372.txt');

    elseif Ndisparo>=398 && Ndisparo < 516
    fid=fopen('osc_channels_398.txt');

    elseif Ndisparo>=516 && Ndisparo < 559
    fid=fopen('osc_channels_516.txt');

    elseif Ndisparo>=559 && Ndisparo<658
    fid=fopen('osc_channels_559.txt');
    
    elseif Ndisparo >= 658 && Ndisparo<954
    fid=fopen('osc_channels_658.txt');
    
    elseif Ndisparo >= 954 && Ndisparo<1487
    fid=fopen('osc_channels_954.txt');
    
    elseif Ndisparo >= 1487 && Ndisparo<1493
    fid=fopen('osc_channels_1487.txt');
    
      elseif Ndisparo >= 1493
    fid=fopen('osc_channels_1493.txt');
    
    
else
end


tline=fgetl(fid);
tlines = cell(0,1);

while ischar(tline)
    tlines{end+1,1} = tline;
    tline = fgetl(fid);
end
fclose(fid);

%asigna los nombres de los canales a las siguientes variable
lab3054=find(strcmp(tlines,'tds3054'));
ch1name3054=tlines(lab3054+1);
ch2name3054=tlines(lab3054+2);
ch3name3054=tlines(lab3054+3);
ch4name3054=tlines(lab3054+4);

lab4104=find(strcmp(tlines,'dpo4104'));
ch1name4104=tlines(lab4104+1);
ch2name4104=tlines(lab4104+2);
ch3name4104=tlines(lab4104+3);
ch4name4104=tlines(lab4104+4);
% 
% labtds5054=find(strcmp(tlines,'tds5054'));
% ch1nametds5054=tlines(labtds5054+1);
% ch2nametds5054=tlines(labtds5054+2);
% ch3nametds5054=tlines(labtds5054+3);
% ch4nametds5054=tlines(labtds5054+4);

labtds5054=find(strcmp(tlines,'tds5054'));
ch1nametds5054=tlines(labtds5054+1);
ch2nametds5054=tlines(labtds5054+2);
ch3nametds5054=tlines(labtds5054+3);
ch4nametds5054=tlines(labtds5054+4);

labtds5104=find(strcmp(tlines,'tds5104'));
ch1nametds5104=tlines(labtds5104+1);
ch2nametds5104=tlines(labtds5104+2);
ch3nametds5104=tlines(labtds5104+3);
ch4nametds5104=tlines(labtds5104+4);

labdpo5054=find(strcmp(tlines,'dpo5054'));
ch1namedpo5054=tlines(labdpo5054+1);
ch2namedpo5054=tlines(labdpo5054+2);
ch3namedpo5054=tlines(labdpo5054+3);
ch4namedpo5054=tlines(labdpo5054+4);


lab7104=find(strcmp(tlines,'tds7104'));
ch1name7104=tlines(lab7104+1);
ch2name7104=tlines(lab7104+2);
ch3name7104=tlines(lab7104+3);
ch4name7104=tlines(lab7104+4);

labtds684b=find(strcmp(tlines,'tds684b'));
ch1nametds684b=tlines(labtds684b+1);
ch2nametds684b=tlines(labtds684b+2);
ch3nametds684b=tlines(labtds684b+3);
ch4nametds684b=tlines(labtds684b+4);

%% carga datos de los osciloscopios

TDS3054=load([shot '_' 'tds3054.txt']);
DPO4104=load([shot '_' 'dpo4104.txt']);
TDS5054=load([shot '_' 'tds5054.txt']);

TDS7104=load([shot '_' 'tds7104.txt']);
%TLS216=load([shot '_' 'tls216.txt']);

TDS684B=load([shot '_' 'tds684b.txt']);
TDS5104=load([shot '_' 'tds5104.txt']);
%TDS5104=load([shot '_' 'tds7154.txt']);%se reemplazo el osc 5104 por el 7154, todo queda igual
DPO5054=load([shot '_' 'dpo5054.txt']);

%% integra rogowski principal en tds7104 (sin integrador externo)
npto4=1000;
t7104=TDS7104(:,1);
dIPr=smooth(TDS7104(:,2),50);
dIPr=dIPr-mean(dIPr(1:npto4));
IPr=cumtrapz(t7104,dIPr)*5.7e7;%el factor aparecce al igualar las corrientes de ambos con y sin integrador externo
 
%% suaviza la corriente principal integrada y multiplica por factor de calibración (con integrador externo)     

IPrIn=smooth(TDS7104(:,3),100);
IPrIn=IPrIn*fPr;%en kA


%% encontrar el tiempo t=0 para que coincida con 0.1IPr(max)

%[IPrmax inPrmax]=findpeaks(IPr,'MinPeakProminence',5) %seleccionar unoss de estos 2
[IPrmax inPrmax]=max(IPr)                             %seleccionar unoss de estos 2
%%
IPr0=5*std(IPrIn(1:npto4))% encuentra el valor del ruido electrico antes de la señal de corriente, y lo multiplica por 5

[ d4, inPr0 ] = min( abs( IPrIn(1:inPrmax)-IPr0 ) );%encuentra el indice para cuando la señal electrica es 5 veces sobre la señal del ruido electrico
tPr0=t7104(inPr0);

IPrIn=IPrIn-mean(IPrIn(round(0.8*inPr0):round(0.9*inPr0)));
IPrmax=max(IPrIn);
%[IPrmax inPrmax]=findpeaks(IPrIn,'MinPeakProminence',20)
[ d10, inPr10 ] = min( abs( IPrIn(1:inPrmax(1))-0.1*IPrmax(1) ) );
[ d90, inPr90 ] = min( abs( IPrIn(1:inPrmax(1))-0.9*IPrmax(1) ) );
I10=IPrIn(inPr10);
I90=IPrIn(inPr90);
t10=t7104(inPr10);
t90=t7104(inPr90);
trise=(t90-t10)*1e9
%% largo de cables

if Ndisparo>=516 && Ndisparo < 559
TC=dlmread('tiempo_cables_516.txt','',1,0)*1e-9;
elseif Ndisparo>=559 && Ndisparo < 658
TC=dlmread('tiempo_cables_559.txt','',1,0)*1e-9;
elseif Ndisparo>=658 && Ndisparo < 954
TC=dlmread('tiempo_cables_658.txt','',1,0)*1e-9;
elseif Ndisparo>=954 && Ndisparo < 1493
TC=dlmread('tiempo_cables_954.txt','',1,0)*1e-9;
elseif Ndisparo>=1493 
TC=dlmread('tiempo_cables_1493.txt','',1,0)*1e-9;

end

Ttds7104_2=TDS7104(:,1)-tPr0;% corriente principal integrada que define t=0
Ttds7104_1=TDS7104(:,1)-tPr0-(TC(1,4)-TC(2,4));
Ttds7104_3=TDS7104(:,1)-tPr0-(TC(3,4)-TC(2,4));
Ttds7104_4=TDS7104(:,1)-tPr0-(TC(4,4)-TC(2,4));

Ttds3054_1=TDS3054(:,1)-tPr0-(TC(1,1)-TC(2,4));
Ttds3054_2=TDS3054(:,1)-tPr0-(TC(2,1)-TC(2,4));
Ttds3054_3=TDS3054(:,1)-tPr0-(TC(3,1)-TC(2,4));
Ttds3054_4=TDS3054(:,1)-tPr0-(TC(4,1)-TC(2,4));

Ttds684b_1=TDS684B(:,1)-tPr0-(TC(1,7)-TC(2,4));
Ttds684b_2=TDS684B(:,1)-tPr0-(TC(2,7)-TC(2,4));
Ttds684b_3=TDS684B(:,1)-tPr0-(TC(3,7)-TC(2,4));
Ttds684b_4=TDS684B(:,1)-tPr0-(TC(4,7)-TC(2,4));

if     Ndisparo<259
       td4104=1.5956e-6;
elseif Ndisparo>=259
       td4104=0;% a partir del disparo 259
end
       

Tdpo4104_1=DPO4104(:,1)+td4104-tPr0-(TC(1,2)-TC(2,4));
Tdpo4104_2=DPO4104(:,1)+td4104-tPr0-(TC(2,2)-TC(2,4));
Tdpo4104_3=DPO4104(:,1)+td4104-tPr0-(TC(3,2)-TC(2,4));
Tdpo4104_4=DPO4104(:,1)+td4104-tPr0-(TC(4,2)-TC(2,4));

Ttds5054_1=TDS5054(:,1)-tPr0-(TC(1,3)-TC(2,4));
Ttds5054_2=TDS5054(:,1)-tPr0-(TC(2,3)-TC(2,4));
Ttds5054_3=TDS5054(:,1)-tPr0-(TC(3,3)-TC(2,4));
Ttds5054_4=TDS5054(:,1)-tPr0-(TC(4,3)-TC(2,4));

tCcoax=42e-9;

Ttds5104_1=TDS5104(:,1)-tPr0-(TC(1,5)-TC(2,4));
Ttds5104_2=TDS5104(:,1)-tPr0-(TC(2,5)-TC(2,4));
Ttds5104_3=TDS5104(:,1)-tPr0-(TC(3,5)-TC(2,4));
Ttds5104_4=TDS5104(:,1)-tPr0-(TC(4,5)-TC(2,4));

%correccion delay caja optica
if     Ndisparo<262
       tpin1norte=182e-9;
       tpin1sur=184e-9;
elseif Ndisparo>=262
       tpin1norte=0;% a partir del disparo 262
       tpin1sur=0;
end


Tdpo5054_1=DPO5054(:,1)-tPr0-(TC(1,6)-TC(2,4));
Tdpo5054_2=DPO5054(:,1)-tPr0-(TC(2,6)-TC(2,4));
Tdpo5054_3=DPO5054(:,1)-tPr0-(TC(3,6)-tpin1norte-TC(2,4));
Tdpo5054_4=DPO5054(:,1)-tPr0-(TC(4,6)-tpin1sur-TC(2,4));

%% analisa las senales de los monitores de voltaje capacitivo en tds 5054

npto=15000;
t5054=TDS5054(:,1);
dVtln=smooth(TDS5054(:,3),100);
dVtln=dVtln-mean(dVtln(1:npto));
dVtlc=smooth(TDS5054(:,4),100);
dVtlc=dVtlc-mean(dVtlc(1:npto));
dVtls=smooth(TDS5054(:,5),100);
dVtls=dVtls-mean(dVtls(1:npto));

flc=2.86*1e10;
fls=flc;
fln=flc;

Vtln=fln*cumtrapz(Ttds5054_2,dVtln);
Vtlc=flc*cumtrapz(Ttds5054_3,dVtlc);
Vtls=fls*cumtrapz(Ttds5054_4,dVtls);
%% integra rogowski R2
dIR2=smooth(TDS5054(:,2),50);
dIR2=dIR2-mean(dIR2(1:npto));

IR2=cumtrapz(Ttds5054_1,dIR2)*fR2/1000;%en kA

% % encontrar el tiempo para que IR1=0.1IR1(max)
% [ImaxR1 inR1max]=max(IR1)
% [ d1, inR1 ] = min( abs( IR1(1:inR1max)-0.1*ImaxR1 ) )
% tR1=t5054(inR1)

%% integra rogowski R1
npto2=3000;
t4104=DPO4104(:,1);
dIR1=smooth(DPO4104(:,2),50);
dIR1=dIR1-mean(dIR1(1:npto2));

IR1=cumtrapz(Tdpo4104_1,dIR1)*fR1/1000;%en kA

% % encontrar el tiempo para que IR2=0.1IR2(max)
% [ImaxR2 inR2max]=max(IR2)
% [ d2, inR2 ] = min( abs( IR2(1:inR2max)-0.1*ImaxR2 ) )
% tR2=t4104(inR2)

%% integra rogowski R3
npto3=1000;
t5104=TDS5104(:,1);
dIR3=smooth(TDS5104(:,2),50);
dIR3=dIR3-mean(dIR3(npto3/2:npto3));

IR3=cumtrapz(Ttds5104_1,dIR3)*fR3/1000;%en kA

% % encontrar el tiempo para que IR2=0.1IR2(max)
% [ImaxR3 inR3max]=max(IR3)
% [ d3, inR3 ] = min( abs( IR3(1:inR3max)-0.1*ImaxR3 ) )
% tR3=t5104(inR3)



%% suma de IR1, IR2 y IR3:
IR=interp1(Ttds5054_1,IR2,Ttds5104_1)+interp1(Tdpo4104_1,IR1,Ttds5104_1)+interp1(Ttds5104_1,IR3,Ttds5104_1);

%% crea un vector de tiempo "absoluto" que usaremos como unico tiempo para todos los datos
ta=-2e-6;
tb=-1e-7;
tc=6e-7;
td=1.5e-6;
dt1=1e-9;
dt2=0.1e-9;

T1=linspace(ta,tb,(tb-ta)/dt1);
T2=linspace(tb+dt2,tc,(tc-tb-dt2)/dt2);
T3=linspace(tc+dt1,td,(td-tc-dt1)/dt1);

T=[T1'; T2'; T3'];
TL=linspace(-2e-3,2e-3,2000);

%% interpola datos a tiempo absoluto T
%TDS3054
TDS3054_ch1=interp1(Ttds3054_1,TDS3054(:,2),T);
TDS3054_ch2=interp1(Ttds3054_2,TDS3054(:,3),T);
TDS3054_ch3=interp1(Ttds3054_3,TDS3054(:,4),T);
TDS3054_ch4=interp1(Ttds3054_4,TDS3054(:,5),T);

%DPO4104
DPO4104_ch1= interp1(Tdpo4104_1,DPO4104(:,2),T);
DPO4104_ch2= interp1(Tdpo4104_2,DPO4104(:,3),T);
DPO4104_ch3= interp1(Tdpo4104_3,DPO4104(:,4),T);
DPO4104_ch4= interp1(Tdpo4104_4,DPO4104(:,5),T);

%TDS5054
TDS5054_ch1=interp1(Ttds5054_1,TDS5054(:,2),T);
TDS5054_ch2=interp1(Ttds5054_2,TDS5054(:,3),T);
TDS5054_ch3=interp1(Ttds5054_3,TDS5054(:,4),T);
TDS5054_ch4=interp1(Ttds5054_4,TDS5054(:,5),T);

%TDS7104
TDS7104_ch1=interp1(Ttds7104_1,IPr,T);%IPr
TDS7104_ch2=interp1(Ttds7104_2,IPrIn,T);%IPrIn
TDS7104_ch3=interp1(Ttds7104_3,TDS7104(:,4),T);
TDS7104_ch4=interp1(Ttds7104_4,TDS7104(:,5),T);

%TDS684B
TDS684B_ch1=interp1(Ttds684b_1,TDS684B(:,2),TL);
TDS684B_ch2=interp1(Ttds684b_2,TDS684B(:,3),TL);
TDS684B_ch3=interp1(Ttds684b_3,TDS684B(:,4),TL);
TDS684B_ch4=interp1(Ttds684b_4,TDS684B(:,5),TL);


%TDS5104
TDS5104_ch1=interp1(Ttds5104_1,TDS5104(:,2),T);
TDS5104_ch2=interp1(Ttds5104_2,TDS5104(:,3),T);
TDS5104_ch3=interp1(Ttds5104_3,TDS5104(:,4),T);
TDS5104_ch4=interp1(Ttds5104_4,TDS5104(:,5),T);

%DPO5054
DPO5054_ch1=interp1(Tdpo5054_1,DPO5054(:,2),T);
DPO5054_ch2=interp1(Tdpo5054_2,DPO5054(:,3),T);
DPO5054_ch3=interp1(Tdpo5054_3,DPO5054(:,4),T);
DPO5054_ch4=interp1(Tdpo5054_4,DPO5054(:,5),T);



%% TDS3054
figure%1
PLOTDEFAULTS
plot(Ttds3054_1,TDS3054(:,2),Ttds3054_2,TDS3054(:,3),Ttds3054_3,TDS3054(:,4),Ttds3054_4,-0.5*smooth(TDS3054(:,5),30),'linewidth',1);
legend(char(ch1name3054),char(ch2name3054),char(ch3name3054),char(ch4name3054),'Location','SouthEast')
title(['tds3054,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[2,15,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-2e-6 1e-6])
%% TDS7104
figure%2
PLOTDEFAULTS
plot(Ttds7104_1,TDS7104(:,2),Ttds7104_2,100*TDS7104(:,3),Ttds7104_3,TDS7104(:,4),Ttds7104_4,TDS7104(:,5));
legend(char(ch1name7104),char(ch2name7104),char(ch3name7104),char(ch4name7104))
title(['tds7104,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[16,15,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-1.5e-6 1e-6])
%% TDS7104 corriente principal integrada
figure%2b
PLOTDEFAULTS
yyaxis left
plot(Ttds7104_1-1e-8,IPr,Ttds7104_2,IPrIn,'-b','LineWidth',1);
ylabel('current/kA')
%ylim([-2 10])

yyaxis right
plot(Ttds7104_3,TDS7104(:,4),'k',Ttds7104_4,TDS7104(:,5),'-r');
ylabel('V')

legend(char(ch1name7104),char(ch2name7104),char(ch3name7104),char(ch4name7104))
title(['tds7104,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[16,15,13,10]);
xlabel('time /s')
xlim([-1e-6 1e-6])
ylim([-1 20])

%% save current Ipr
Isave=[Ttds7104_1-1e-8 IPr]
%%
name=[shot '_' 'Ipr.txt'];
save(name,'Isave','-ascii')
%% TDS5054
figure%3
PLOTDEFAULTS
plot(Ttds5054_1,TDS5054(:,2),Ttds5054_2,dVtln*3,Ttds5054_3,dVtlc*3,Ttds5054_4,dVtls*10,'linewidth',1);
legend(char(ch1nametds5054),char(ch2nametds5054),char(ch3nametds5054),char(ch4nametds5054))
title(['tds5054,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[30,15,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-0.5e-6 1e-6])
%% TDS5054 integrados
figure%4
PLOTDEFAULTS
yyaxis left
plot(Ttds5054_1,IR2,'LineWidth',1);
ylabel('current/kA')
ylim([-60 60])

yyaxis right
plot(Ttds5054_4,Vtls*6,'-k',Ttds5054_3,Vtlc,'-r',Ttds5054_2,Vtln,'-b','LineWidth',1);
ylabel('V')

legend('IR2','Vsur','Vcamara','Vnorte')
title(['tds5054,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[30,2,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-0.5e-6 1e-6])

%% TDS5054 integrados
figure%4b
PLOTDEFAULTS
yyaxis left
plot(Ttds5054_1,-dIR2,'k','LineWidth',3);
ylabel('current/kA')
ylim([-25 25])

yyaxis right
plot(Ttds5054_4,Vtls*6,'-k',Ttds5054_3,2*Vtlc,'-r',Ttds5054_2,Vtln,'-b','LineWidth',1);
ylabel('V')

legend('dIR2','Vsur','Vcamara','Vnorte')
title(['tds5054,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[30,2,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-0.5e-6 1.5e-6])
%ylim([-8e-7 8e-7])

%% DPO4104
figure%5
PLOTDEFAULTS
plot(Tdpo4104_1,DPO4104(:,2),Tdpo4104_2,DPO4104(:,3),Tdpo4104_3,DPO4104(:,4),Tdpo4104_4,DPO4104(:,5),'linewidth',1);
legend(char(ch1name4104),char(ch2name4104),char(ch3name4104),char(ch4name4104))
title(['DPO4104,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[16,2,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-0.5e-6 1e-6])
%% DPO4104 corriente IR1 integrada 
figure%5b
PLOTDEFAULTS
yyaxis left
plot(Tdpo4104_1,IR1,'LineWidth',1.5);
ylabel('current/kA)')
ylim([-20 40])

yyaxis right
plot(Tdpo4104_2,DPO4104(:,3),'k',Tdpo4104_3,DPO4104(:,4),'-r',Tdpo4104_4,smooth(DPO4104(:,5),10),'-b','linewidth',1);
ylabel('V')
ylim([-1 5])

legend(char(ch1name4104),char(ch2name4104),char(ch3name4104),char(ch4name4104))
title(['DPO4104,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[16,2,13,10]);
xlabel('time /s')
%xlim([-0.5e-6 1e-6])


%% TDS5104-DPO5054
figure%6
PLOTDEFAULTS
plot(Ttds5104_1,TDS5104(:,2),Ttds5104_2,TDS5104(:,3),Ttds5104_3,TDS5104(:,4),Ttds5104_4,TDS5104(:,5),Tdpo5054_1,DPO5054(:,2),Tdpo5054_2,DPO5054(:,3),'LineWidth',1);
legend(char(ch1nametds5104),char(ch2nametds5104),char(ch3nametds5104),char(ch4nametds5104),char(ch1namedpo5054),char(ch2namedpo5054))
title(['5104-dpo5054,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[2,2,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-2e-6 1.5e-6])
ylim([-3 1])
%% TDS5104 corriente IR3 integrada
figure%6b
PLOTDEFAULTS
plot(Ttds5104_2,TDS5104(:,3),Ttds5104_3,TDS5104(:,4),Ttds5104_4,TDS5104(:,5),Tdpo5054_1,DPO5054(:,2),Tdpo5054_2,DPO5054(:,3),Tdpo5054_3,DPO5054(:,4)*10,Tdpo5054_4,DPO5054(:,5),'LineWidth',1);
ylabel('V')
legend(char(ch2nametds5104),char(ch3nametds5104),char(ch4nametds5104),char(ch1namedpo5054),char(ch2namedpo5054),char(ch3namedpo5054),char(ch4namedpo5054))


title(['tls5104-dpo5054 B,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[2,2,13,10]);
xlabel('time /s')
xlim([-2e-6 1.0e-6])

%% TDS684B
figure
PLOTDEFAULTS
yyaxis left
Cal_IGP=6.857e4;
plot(Ttds684b_2,TDS684B(:,3)*Cal_IGP/1000,'linewidth',1);
ylabel('kA')
%legend(char(ch2nametds684b))
yyaxis right
plot(Ttds684b_1,TDS684B(:,2),Ttds684b_3,TDS684B(:,4),Ttds684b_4,TDS684B(:,5)/10,'linewidth',1);
legend(char(ch2nametds684b),char(ch1nametds684b),char(ch3nametds684b),char(ch4nametds684b))

title(['tds684b,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])
set(gcf,'Units','centimeters','Position',[30,15,13,10]);
xlabel('time /s')
ylabel('V')
xlim([-1.2e-3 0.5e-3])
%% current comparison
figure
PLOTDEFAULTS
plot(Ttds7104_2,IPrIn,Ttds5054_1,20*IR2,Tdpo4104_1,20*IR1,Ttds5104_1,20*IR3,Ttds5104_1,6.5*IR,'LineWidth',1.5)
legend('Iprin','IR2*20','IR1*20','IR3*20','IR*6.5')
xlabel('time/s')
ylabel('current/kA')
xlim([-0.5e-6 1e-6])
text(-0.4e-6,200,strcat('Imax=',num2str(round(IPrmax)),'kA'),'fontsize',14)
set(gcf,'Units','centimeters','Position',[2,15,13,10]);
title(['Corrientes,' ' ' 'shot' ' ' num2str(Ndisparo) ' ' 'fecha:' ' ' fecha])






%% save analyzed data to folver /osc_data_analizado
% currentFolder = pwd;
% 
% cd([currentFolder,'/osc_data_analizado'])
% save(['shot',num2str(Ndisparo),'_','T','.txt'],'T','-ascii')
% save(['shot',num2str(Ndisparo),'_','TL','.txt'],'T','-ascii')
% 
% save(['shot',num2str(Ndisparo),'_',char(ch1name3054),'.txt'],'TDS3054_ch1','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch2name3054),'.txt'],'TDS3054_ch2','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch3name3054),'.txt'],'TDS3054_ch3','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch4name3054),'.txt'],'TDS3054_ch4','-ascii')
% 
% save(['shot',num2str(Ndisparo),'_',char(ch1name4104),'.txt'],'DPO4104_ch1','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch2name4104),'.txt'],'DPO4104_ch2','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch3name4104),'.txt'],'DPO4104_ch3','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch4name4104),'.txt'],'DPO4104_ch4','-ascii')
% 
% save(['shot',num2str(Ndisparo),'_',char(ch1nametds5054),'.txt'],'TDS5054_ch1','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch2nametds5054),'.txt'],'TDS5054_ch2','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch3nametds5054),'.txt'],'TDS5054_ch3','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch4nametds5054),'.txt'],'TDS5054_ch4','-ascii')
% 
% save(['shot',num2str(Ndisparo),'_','IPr','.txt'],'TDS7104_ch1','-ascii')
% save(['shot',num2str(Ndisparo),'_','IPrIn','.txt'],'TDS7104_ch2','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch3name7104),'.txt'],'TDS7104_ch3','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch4name7104),'.txt'],'TDS7104_ch4','-ascii')
% 
% save(['shot',num2str(Ndisparo),'_',char(ch1nametds684b),'.txt'],'TDS684B_ch1','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch2nametds684b),'.txt'],'TDS684B_ch2','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch3nametds684b),'.txt'],'TDS684B_ch3','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch4nametds684b),'.txt'],'TDS684B_ch4','-ascii')
% 
% save(['shot',num2str(Ndisparo),'_',char(ch1nametds5104),'.txt'],'TDS5104_ch1','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch2nametds5104),'.txt'],'TDS5104_ch2','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch3nametds5104),'.txt'],'TDS5104_ch3','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch4nametds5105),'.txt'],'TDS5104_ch4','-ascii')
% 
% save(['shot',num2str(Ndisparo),'_',char(ch1namedpo5054),'.txt'],'DPO5054_ch1','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch2namedpo5054),'.txt'],'DPO5054_ch2','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch3namedpo5054),'.txt'],'DPO5054_ch3','-ascii')
% save(['shot',num2str(Ndisparo),'_',char(ch4namedpo5054),'.txt'],'DPO5054_ch4','-ascii')
% 
% cd(currentFolder)
%%

