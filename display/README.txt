/*zh-CN*/

cd example

测试0inch96屏幕1：sudo python 0inch96_spi0ce0.py

测试0inch96屏幕2：sudo python 0inch96_spi0ce1.py

测试1inch3屏幕：sudo python 1inch3_spi1ce0.py
（运行此命令前需要将dtoverlay=spi1-1cs添加到config.txt文件以打开SPI1设备）

两个0.96inch屏幕同时显示：sudo python double_0inch96_spi.py

两个0.96屏幕同时显示CPU信息：sudo python3 CPU.py

按键测试：sudo python3 key_double.py


/*en-US*/
Test the first screen of 0inch96: sudo python 0inch96_spi0ce0.py

Test the second screen of 0inch96:sudo python 0inch96_spi0ce1.py

Test 1inch3 screen: sudo python 1inch3_spi1ce0.py
(Before running this command, you need to add dtoverlay=spi1-1cs to the config.txt file to open the SPI1 device)

Display two 0.96inch screens at the same time: sudo python double_0inch96_spi.py

Display two 0.96 screens CPU information at the same time: sudo python CPU.py

Test the key：sudo python key_double.py



/*The latest update date is Oct 28th ,2023*/
