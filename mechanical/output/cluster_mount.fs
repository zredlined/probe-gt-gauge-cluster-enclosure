
annotation { "Feature Type Name" : "Cluster cage mount" }
export const clusterCageMount = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Bar clamps + struts" } definition.buildClamps is boolean;
        annotation { "Name" : "Upright clamp" } definition.buildUpright is boolean;
        annotation { "Name" : "Pitch stay" } definition.buildStay is boolean;
        annotation { "Name" : "Column support stubs (reference)" } definition.buildStubs is boolean;
    }
    {
        var step = "start";
        try
        {
        if (definition.buildClamps)
        {
        step = "2";
        const b1 = mkCyl(context, id + "cy2", vector(112.000, 0.000, 0.000), vector(142.000, 0.000, 0.000), 64.000);
        step = "4";
        const b3 = mkBox(context, id + "bx4", 112.000, -43.000, -11.000, 142.000, 43.000, 11.000);
        step = "6";
        const b5 = mkCyl(context, id + "cy6", vector(112.000, -36.000, 0.000), vector(142.000, -36.000, 0.000), 22.000);
        step = "8";
        const b7 = mkCyl(context, id + "cy8", vector(112.000, 36.000, 0.000), vector(142.000, 36.000, 0.000), 22.000);
        step = "10";
        const u9 = mkUnite(context, id + "un10", [b1, b3]);
        step = "12";
        const u11 = mkUnite(context, id + "un12", [u9, b5]);
        step = "14";
        const u13 = mkUnite(context, id + "un14", [u11, b7]);
        step = "16";
        const b15 = mkCyl(context, id + "cy16", vector(111.000, 0.000, 0.000), vector(143.000, 0.000, 0.000), 44.850);
        step = "18";
        const b17 = mkCyl(context, id + "cy18", vector(127.000, -36.000, -40.000), vector(127.000, -36.000, 40.000), 6.400);
        step = "20";
        const b19 = mkCyl(context, id + "cy20", vector(127.000, 36.000, -40.000), vector(127.000, 36.000, 40.000), 6.400);
        step = "22";
        const b21 = mkBox(context, id + "bx22", 111.000, -80.000, -0.500, 143.000, 80.000, 0.500);
        step = "24";
        mkCut(context, id + "ct23", u13, [b15, b17, b19, b21]);
        step = "26";
        opPattern(context, id + "pt25", { "entities" : u13, "transforms" : [identityTransform()], "instanceNames" : ["c"] });
        step = "28";
        const cp24 = qCreatedBy(id + "pt25", EntityType.BODY);
        step = "30";
        const b26 = mkBox(context, id + "bx27", 111.000, -80.000, -80.000, 143.000, 80.000, 0.000);
        step = "32";
        mkIntersect(context, id + "it28", cp24, [b26]);
        step = "34";
        const b29 = mkBox(context, id + "bx30", 111.000, -80.000, 0.000, 143.000, 80.000, 80.000);
        step = "36";
        mkIntersect(context, id + "it31", u13, [b29]);
        step = "38";
        const b32 = mkBox(context, id + "bx33", 107.000, -8.000, 0.000, 147.000, 8.000, 148.827);
        step = "40";
        opTransform(context, id + "rx34", { "bodies" : b32, "transform" : rotationAround(line(vector(0, 0.000, 0.000) * millimeter, vector(1, 0, 0)), 42.215 * degree) });
        step = "42";
        const b35 = mkBox(context, id + "bx36", 87.000, -200.000, 0.500, 167.000, 200.000, 200.000);
        step = "44";
        mkIntersect(context, id + "it37", b32, [b35]);
        step = "46";
        const b38 = mkCyl(context, id + "cy39", vector(107.000, -100.000, 110.225), vector(147.000, -100.000, 110.225), 34.000);
        step = "48";
        const u40 = mkUnite(context, id + "un41", [b32, b38]);
        step = "50";
        const b42 = mkBox(context, id + "bx43", 114.700, -132.000, 98.225, 139.300, -68.000, 150.225);
        step = "52";
        const b44 = mkCyl(context, id + "cy45", vector(87.000, -100.000, 110.225), vector(167.000, -100.000, 110.225), 8.400);
        step = "54";
        mkCut(context, id + "ct46", u40, [b42, b44]);
        step = "56";
        const u47 = mkUnite(context, id + "un48", [u13, u40]);
        step = "58";
        nameBody(context, cp24, "Bar clamp lower L", color(0.184, 0.192, 0.212));
        step = "60";
        nameBody(context, u47, "Bar clamp upper L", color(0.184, 0.192, 0.212));
        step = "62";
        const b49 = mkCyl(context, id + "cy50", vector(422.000, 0.000, 0.000), vector(452.000, 0.000, 0.000), 64.000);
        step = "64";
        const b51 = mkBox(context, id + "bx52", 422.000, -43.000, -11.000, 452.000, 43.000, 11.000);
        step = "66";
        const b53 = mkCyl(context, id + "cy54", vector(422.000, -36.000, 0.000), vector(452.000, -36.000, 0.000), 22.000);
        step = "68";
        const b55 = mkCyl(context, id + "cy56", vector(422.000, 36.000, 0.000), vector(452.000, 36.000, 0.000), 22.000);
        step = "70";
        const u57 = mkUnite(context, id + "un58", [b49, b51]);
        step = "72";
        const u59 = mkUnite(context, id + "un60", [u57, b53]);
        step = "74";
        const u61 = mkUnite(context, id + "un62", [u59, b55]);
        step = "76";
        const b63 = mkCyl(context, id + "cy64", vector(421.000, 0.000, 0.000), vector(453.000, 0.000, 0.000), 44.850);
        step = "78";
        const b65 = mkCyl(context, id + "cy66", vector(437.000, -36.000, -40.000), vector(437.000, -36.000, 40.000), 6.400);
        step = "80";
        const b67 = mkCyl(context, id + "cy68", vector(437.000, 36.000, -40.000), vector(437.000, 36.000, 40.000), 6.400);
        step = "82";
        const b69 = mkBox(context, id + "bx70", 421.000, -80.000, -0.500, 453.000, 80.000, 0.500);
        step = "84";
        mkCut(context, id + "ct71", u61, [b63, b65, b67, b69]);
        step = "86";
        opPattern(context, id + "pt73", { "entities" : u61, "transforms" : [identityTransform()], "instanceNames" : ["c"] });
        step = "88";
        const cp72 = qCreatedBy(id + "pt73", EntityType.BODY);
        step = "90";
        const b74 = mkBox(context, id + "bx75", 421.000, -80.000, -80.000, 453.000, 80.000, 0.000);
        step = "92";
        mkIntersect(context, id + "it76", cp72, [b74]);
        step = "94";
        const b77 = mkBox(context, id + "bx78", 421.000, -80.000, 0.000, 453.000, 80.000, 80.000);
        step = "96";
        mkIntersect(context, id + "it79", u61, [b77]);
        step = "98";
        const b80 = mkBox(context, id + "bx81", 417.000, -8.000, 0.000, 457.000, 8.000, 148.827);
        step = "100";
        opTransform(context, id + "rx82", { "bodies" : b80, "transform" : rotationAround(line(vector(0, 0.000, 0.000) * millimeter, vector(1, 0, 0)), 42.215 * degree) });
        step = "102";
        const b83 = mkBox(context, id + "bx84", 397.000, -200.000, 0.500, 477.000, 200.000, 200.000);
        step = "104";
        mkIntersect(context, id + "it85", b80, [b83]);
        step = "106";
        const b86 = mkCyl(context, id + "cy87", vector(417.000, -100.000, 110.225), vector(457.000, -100.000, 110.225), 34.000);
        step = "108";
        const u88 = mkUnite(context, id + "un89", [b80, b86]);
        step = "110";
        const b90 = mkBox(context, id + "bx91", 424.700, -132.000, 98.225, 449.300, -68.000, 150.225);
        step = "112";
        const b92 = mkCyl(context, id + "cy93", vector(397.000, -100.000, 110.225), vector(477.000, -100.000, 110.225), 8.400);
        step = "114";
        mkCut(context, id + "ct94", u88, [b90, b92]);
        step = "116";
        const u95 = mkUnite(context, id + "un96", [u61, u88]);
        step = "118";
        nameBody(context, cp72, "Bar clamp lower R", color(0.184, 0.192, 0.212));
        step = "120";
        nameBody(context, u95, "Bar clamp upper R", color(0.184, 0.192, 0.212));
        }
        if (definition.buildUpright)
        {
        step = "125";
        const b97 = mkCyl(context, id + "cy98", vector(-0.356, -1.061, 48.000), vector(-0.356, -1.061, 76.000), 64.000);
        step = "127";
        const b99 = mkBox(context, id + "bx100", -11.356, -44.061, 48.000, 10.644, 41.939, 76.000);
        step = "129";
        const b101 = mkCyl(context, id + "cy102", vector(-0.356, -37.061, 48.000), vector(-0.356, -37.061, 76.000), 22.000);
        step = "131";
        const b103 = mkCyl(context, id + "cy104", vector(-0.356, 34.939, 48.000), vector(-0.356, 34.939, 76.000), 22.000);
        step = "133";
        const u105 = mkUnite(context, id + "un106", [b97, b99]);
        step = "135";
        const u107 = mkUnite(context, id + "un108", [u105, b101]);
        step = "137";
        const u109 = mkUnite(context, id + "un110", [u107, b103]);
        step = "139";
        const b111 = mkCyl(context, id + "cy112", vector(-0.356, -1.061, 47.000), vector(-0.356, -1.061, 77.000), 44.850);
        step = "141";
        const b113 = mkCyl(context, id + "cy114", vector(-40.356, -37.061, 62.000), vector(39.644, -37.061, 62.000), 6.400);
        step = "143";
        const b115 = mkCyl(context, id + "cy116", vector(-40.356, 34.939, 62.000), vector(39.644, 34.939, 62.000), 6.400);
        step = "145";
        const b117 = mkBox(context, id + "bx118", -0.856, -81.061, 47.000, 0.144, 78.939, 77.000);
        step = "147";
        mkCut(context, id + "ct119", u109, [b111, b113, b115, b117]);
        step = "149";
        opPattern(context, id + "pt121", { "entities" : u109, "transforms" : [identityTransform()], "instanceNames" : ["c"] });
        step = "151";
        const cp120 = qCreatedBy(id + "pt121", EntityType.BODY);
        step = "153";
        const b122 = mkBox(context, id + "bx123", -80.356, -81.061, 47.000, -0.356, 78.939, 77.000);
        step = "155";
        mkIntersect(context, id + "it124", cp120, [b122]);
        step = "157";
        const b125 = mkBox(context, id + "bx126", -0.356, -81.061, 47.000, 79.644, 78.939, 77.000);
        step = "159";
        mkIntersect(context, id + "it127", u109, [b125]);
        step = "161";
        const b128 = mkBox(context, id + "bx129", 28.000, -11.061, 48.000, 61.698, 8.939, 76.000);
        step = "163";
        const u130 = mkUnite(context, id + "un131", [u109, b128]);
        step = "165";
        const b132 = mkCyl(context, id + "cy133", vector(33.698, -1.061, 62.000), vector(62.698, -1.061, 62.000), 6.400);
        step = "167";
        mkCut(context, id + "ct134", u130, [b132]);
        step = "169";
        nameBody(context, cp120, "Upright clamp outboard", color(0.184, 0.192, 0.212));
        step = "171";
        nameBody(context, u130, "Upright clamp inboard", color(0.184, 0.192, 0.212));
        }
        if (definition.buildStay)
        {
        step = "176";
        const b135 = mkBox(context, id + "bx136", 61.698, -1.061, 54.000, 69.698, 143.914, 70.000);
        step = "178";
        const b137 = mkCyl(context, id + "cy138", vector(61.698, -1.061, 62.000), vector(69.698, -1.061, 62.000), 16.000);
        step = "180";
        const b139 = mkCyl(context, id + "cy140", vector(61.698, 143.914, 62.000), vector(69.698, 143.914, 62.000), 16.000);
        step = "182";
        const u141 = mkUnite(context, id + "un142", [b135, b137]);
        step = "184";
        const u143 = mkUnite(context, id + "un144", [u141, b139]);
        step = "186";
        const b145 = mkBox(context, id + "bx146", 60.698, 131.914, 58.800, 70.698, 155.914, 65.200);
        step = "188";
        const b147 = mkCyl(context, id + "cy148", vector(60.698, 131.914, 62.000), vector(70.698, 131.914, 62.000), 6.400);
        step = "190";
        const b149 = mkCyl(context, id + "cy150", vector(60.698, 155.914, 62.000), vector(70.698, 155.914, 62.000), 6.400);
        step = "192";
        const u151 = mkUnite(context, id + "un152", [b145, b147]);
        step = "194";
        const u153 = mkUnite(context, id + "un154", [u151, b149]);
        step = "196";
        const b155 = mkCyl(context, id + "cy156", vector(60.698, -1.061, 62.000), vector(70.698, -1.061, 62.000), 6.400);
        step = "198";
        mkCut(context, id + "ct157", u143, [b155, u153]);
        step = "200";
        opTransform(context, id + "rx158", { "bodies" : u143, "transform" : rotationAround(line(vector(0, -1.061, 62.000) * millimeter, vector(1, 0, 0)), 125.492 * degree) });
        step = "202";
        nameBody(context, u143, "Pitch stay", color(0.435, 0.247, 0.749));
        }
        if (definition.buildStubs)
        {
        step = "207";
        const b159 = mkCyl(context, id + "cy160", vector(193.564, 22.973, 11.099), vector(215.800, -157.900, -10.300), 44.450);
        step = "209";
        nameBody(context, b159, "Cage stub L", color(0.690, 0.550, 0.230));
        step = "211";
        const b161 = mkCyl(context, id + "cy162", vector(329.154, 21.282, 9.322), vector(322.300, -155.600, -11.000), 44.450);
        step = "213";
        nameBody(context, b161, "Cage stub R", color(0.690, 0.550, 0.230));
        }
        }
        catch (e)
        {
            fCuboid(context, id + "errbox", { "corner1" : vector(600, -100, 0) * millimeter, "corner2" : vector(610, -90, 10) * millimeter });
            setProperty(context, { "entities" : qCreatedBy(id + "errbox", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "FAILED step " ~ step ~ ": " ~ toString(e) });
        }
    }, { buildClamps : true, buildUpright : true, buildStay : true, buildStubs : true });
